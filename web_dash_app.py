"""
Web-based annotation interface for event extraction using Dash.

Features:
- File upload (JSON with document strings)
- Dataset/schema selection (geneva, wikievents, casie, genia2013, m2e2, rams)
- Model type selection (domain-specific or cross-domain)
- Event detection (pipeline, e2e, merged modes with highlighting)
- Argument extraction (with argument highlighting and roles)
- Multi-dataset annotation for same document
- Result saving with hierarchical dataset organization
"""

import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import traceback
import base64

import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

import torch
from transformers import T5ForConditionalGeneration, AutoTokenizer

# Import functions from web_infer.py
from infer import (
    run_single_inference_event_detection,
    parse_and_merge_single_inference_event_detection_results,
    run_single_inference_event_argument_extraction,
    structure_argument_extraction_pipeline_predictions,
    parse_argument_extraction,
    run_single_inference_event_extraction_e2e,
    present_parsed_output,
    DATASETS
)

from pattern_tagprime import patterns

# Colors for highlighting
TRIGGER_COLORS = {
    "pipeline": "#fff3cd",     # Yellow
    "e2e": "#cfe2ff",          # Blue
    "merged": "#d1e7dd"        # Green
}
ROLE_COLORS = ["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#ff99cc", "#c2c2f0"]
MODEL_TYPES = ["domain-specific", "cross-domain"]
EXAMPLE_TEXT = "Argentina rejects reports that it has transferred uranium enrichment techniques to Iran (2958)."

MODEL_PATHS = {'geneva': "sili03/EE_geneva",
               'wikievents': "sili03/EE_wikievents",
               'casie': "sili03/EE_casie",
               'genia2013': "sili03/EE_genia2013",
               'm2e2': "sili03/EE_m2e2",
               'rams': "sili03/EE_rams",
               'cross-domain': "sili03/EE_cross_domain"}

class ModelCache:
    """Caches loaded models to avoid reloading."""
    def __init__(self):
        self.models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def get_model(self, model_type: str, tokenizer_dir: str, model_dir: str):
        """Load or retrieve cached model."""
        key = (model_type, model_dir)
        if key not in self.models:
            print(f"Loading model: {model_type} from {model_dir}")
            model = T5ForConditionalGeneration.from_pretrained(model_dir)
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
            model.to(self.device)
            model.eval()
            self.models[key] = (model, tokenizer)
        return self.models[key]


# Global model cache
model_cache = ModelCache()


def get_model_path(model_type: str, dataset: str) -> Tuple[str, str]:
    """Get tokenizer and model directory paths based on model type and dataset."""
    tokenizer_dir = "google-t5/t5-base"

    model_key = "cross-domain" if model_type == "cross-domain" else dataset
    model_dir = MODEL_PATHS.get(model_key)
    if not model_dir:
        raise ValueError(f"Model path not configured for key: {model_key}")

    return tokenizer_dir, model_dir


def is_local_model_path(model_dir: str) -> bool:
    """Return True if the model path should be validated as a local filesystem path."""
    return model_dir.startswith(("/", "./", "../", "~"))


def validate_model_path(model_dir: str) -> Optional[str]:
    """Return an error message if a local model path is missing, otherwise None."""
    if is_local_model_path(model_dir):
        expanded = Path(model_dir).expanduser()
        if not expanded.exists():
            return f"Error: Model directory not found: {expanded}"
    return None


def create_event_card(event: Dict, title: str = "Event") -> dbc.Card:
    """Create a card displaying a complete event."""
    trigger = event.get("trigger", {})
    arguments = event.get("arguments", [])
    
    trigger_text = trigger.get("text", "N/A")
    trigger_type = trigger.get("type", "N/A")
    trigger_offset = trigger.get("offset", [])
    
    # Build arguments list
    arg_items = []
    for i, arg in enumerate(arguments):
        arg_text = arg.get("text", "N/A")
        arg_role = arg.get("role", "N/A")
        arg_offset = arg.get("offset", [])
        
        arg_items.append(
            html.Div([
                html.Strong(f"{arg_role}: "),
                html.Span(arg_text),
                html.Small(f" {arg_offset}", className="text-muted ms-2")
            ], style={"marginBottom": "8px"})
        )
    
    return dbc.Card([
        dbc.CardHeader(html.H6(f"{title} - {trigger_type}", className="mb-0")),
        dbc.CardBody([
            html.Div([
                html.Strong("Trigger: "),
                html.Mark(trigger_text, style={"backgroundColor": TRIGGER_COLORS["pipeline"], "padding": "2px 4px", "borderRadius": "3px"}),
                html.Small(f" {trigger_offset}", className="text-muted ms-2")
            ], style={"marginBottom": "15px"}),
            html.Div([
                html.Strong("Arguments:"),
                html.Div(arg_items if arg_items else [html.P("No arguments", className="text-muted")], style={"marginTop": "10px"})
            ])
        ])
    ], className="mb-2", style={"borderLeft": "4px solid #0d6efd"})


def create_source_display(source: str, triggers_by_mode: Dict[str, List]) -> html.Div:
    """Create a display showing source text with highlights for different modes."""
    if not source:
        return html.P("No source text", className="text-muted")
    
    def create_mode_display(mode: str, triggers: List, color: str) -> html.Div:
        """Create annotated text display for a single mode."""
        if not triggers:
            return html.P(source, style={
                "padding": "10px",
                "backgroundColor": "#f5f5f5",
                "borderRadius": "4px",
                "fontFamily": "monospace",
                "lineHeight": "1.8"
            })
        
        # Build offset map for this mode
        offset_map = {}
        for trigger_tuple in triggers:
            if isinstance(trigger_tuple, (list, tuple)) and len(trigger_tuple) >= 3:
                text, event_type, offset = trigger_tuple[0], trigger_tuple[1], trigger_tuple[2]
                if offset and isinstance(offset, (list, tuple)) and len(offset) == 2:
                    offset_key = tuple(offset)
                    offset_map[offset_key] = (text, event_type)
        
        if not offset_map:
            return html.P(source, style={
                "padding": "10px",
                "backgroundColor": "#f5f5f5",
                "borderRadius": "4px",
                "fontFamily": "monospace",
                "lineHeight": "1.8"
            })
        
        # Build highlighted text with badges
        sorted_offsets = sorted(offset_map.keys(), key=lambda x: x[0])
        elements = []
        last_end = 0
        
        for start, end in sorted_offsets:
            # Add text before highlight
            if start > last_end:
                elements.append(html.Span(source[last_end:start]))
            
            text, event_type = offset_map[(start, end)]
            
            # Create highlighted span with badge
            elements.append(html.Span([
                html.Mark(
                    source[start:end+1],
                    style={
                        "backgroundColor": color,
                        "padding": "2px 4px",
                        "borderRadius": "3px",
                        "fontWeight": "bold"
                    }
                ),
                dbc.Badge(
                    event_type,
                    color="primary",
                    pill=True,
                    className="ms-1",
                    style={"fontSize": "0.7em", "verticalAlign": "super"}
                )
            ]))
            last_end = end + 1
        
        # Add remaining text
        if last_end < len(source):
            elements.append(html.Span(source[last_end:]))
        
        return html.Div(elements, style={
            "padding": "10px",
            "backgroundColor": "#f5f5f5",
            "borderRadius": "4px",
            "lineHeight": "2.2",
            "fontFamily": "monospace"
        })
    
    # Create displays for each mode
    pipeline_display = create_mode_display("pipeline", triggers_by_mode.get("pipeline", []), TRIGGER_COLORS["pipeline"])
    e2e_display = create_mode_display("e2e", triggers_by_mode.get("e2e", []), TRIGGER_COLORS["e2e"])
    merged_display = create_mode_display("merged", triggers_by_mode.get("merged", []), TRIGGER_COLORS["merged"])
    
    # Return tabs with three modes
    return dbc.Tabs([
        dbc.Tab(label="Pipeline Mode", children=[
            html.Div(pipeline_display, className="mt-2")
        ]),
        dbc.Tab(label="E2E Mode", children=[
            html.Div(e2e_display, className="mt-2")
        ]),
        dbc.Tab(label="Merged Mode", children=[
            html.Div(merged_display, className="mt-2")
        ])
    ])


def _color_from_palette(label: str, palette: List[str]) -> str:
    """Deterministically pick a color for a label."""
    if not palette:
        return "#d3d3d3"
    return palette[sum(ord(ch) for ch in label) % len(palette)]


def create_combined_annotation_display(source: str, ae_results_by_mode: Dict) -> html.Div:
    """Create display with triggers and arguments using same color per event. Triggers highlighted, arguments framed."""
    if not source:
        return html.P("No source text", className="text-muted")
    
    # Event-based colors (same color for all annotations of same event)
    EVENT_COLORS = ["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#ff99cc", "#c2c2f0"]
    
    def get_event_color(event_num):
        """Get color for event based on event number."""
        return EVENT_COLORS[(event_num - 1) % len(EVENT_COLORS)]
    
    def create_mode_combined_display(mode: str, events: List[Dict]) -> html.Div:
        """Create annotated text with triggers highlighted and arguments framed, with badges next to/below."""
        if not events:
            return html.Div([
                html.Pre(source, style={
                    "padding": "10px",
                    "backgroundColor": "#f5f5f5",
                    "borderRadius": "4px",
                    "fontFamily": "monospace",
                    "fontSize": "0.95em"
                })
            ])
        
        # Collect all annotations with positions
        triggers_by_pos = {}  # {(start, end): [trigger_info, ...]}
        arguments_by_pos = {}  # {(start, end): [arg_info, ...]}
        
        for event_idx, event in enumerate(events):
            event_num = event_idx + 1
            event_color = get_event_color(event_num)
            
            # Add trigger annotation
            trigger = event.get("trigger", {})
            trigger_offset = trigger.get("offset", [])
            if trigger_offset and len(trigger_offset) == 2:
                start, end = trigger_offset[0], trigger_offset[1]
                if (start, end) not in triggers_by_pos:
                    triggers_by_pos[(start, end)] = []
                triggers_by_pos[(start, end)].append({
                    "text": trigger.get("text", ""),
                    "type": trigger.get("type", ""),
                    "event_num": event_num,
                    "color": event_color
                })
            
            # Collect arguments by position
            for arg in event.get("arguments", []):
                arg_offset = arg.get("offset", [])
                if arg_offset and len(arg_offset) == 2:
                    start, end = arg_offset[0], arg_offset[1]
                    if (start, end) not in arguments_by_pos:
                        arguments_by_pos[(start, end)] = []
                    arguments_by_pos[(start, end)].append({
                        "text": arg.get("text", ""),
                        "label": arg.get("role", ""),
                        "event_num": event_num,
                        "color": event_color
                    })
        
        # Build annotated text
        components = []
        last_end = 0
        
        # Collect all annotation positions in order
        all_positions = sorted(
            set(list(triggers_by_pos.keys()) + list(arguments_by_pos.keys()))
        )
        
        for start, end in all_positions:
            # Add plain text before annotation
            if start > last_end:
                components.append(html.Span(source[last_end:start]))
            
            # Get annotations for this position
            trigger_list = triggers_by_pos.get((start, end), [])
            args_list = arguments_by_pos.get((start, end), [])
            
            # Create annotation element
            if trigger_list:
                # Trigger(s): highlighted with colored background + type badges next to it
                trigger_badges = []
                for trigger_info in trigger_list:
                    trigger_badges.append(
                        html.Span(
                            f"E{trigger_info['event_num']}-{trigger_info['type']}",
                            style={
                                "backgroundColor": trigger_info["color"],
                                "fontSize": "0.65em",
                                "marginLeft": "4px",
                                "display": "inline-block",
                                "color": "black",
                                "padding": "2px 6px",
                                "borderRadius": "12px",
                                "border": "none"
                            }
                        )
                    )
                
                # Use first trigger's color
                trigger_color = trigger_list[0]["color"]
                
                # Build trigger element: word + badges on same line
                trigger_element = html.Span([
                    html.Mark(
                        source[start:end+1],
                        style={
                            "backgroundColor": trigger_color,
                            "padding": "2px 4px",
                            "borderRadius": "3px",
                            "fontWeight": "bold",
                            "border": f"2px solid {trigger_color}"
                        }
                    )
                ] + trigger_badges, style={"display": "inline-block", "marginRight": "2px", "whiteSpace": "nowrap"})
                
                # If there are arguments, add them on next line
                if args_list:
                    arg_badges = [
                        html.Span(
                            f"E{arg['event_num']}-Arg-{arg['label']}",
                            style={
                                "backgroundColor": arg["color"],
                                "fontSize": "0.65em",
                                "marginRight": "2px",
                                "display": "inline-block",
                                "color": "black",
                                "padding": "2px 6px",
                                "borderRadius": "12px",
                                "border": "none"
                            }
                        ) for arg in args_list
                    ]
                    
                    components.append(html.Span([
                        trigger_element,
                        html.Br(),
                        html.Div(arg_badges, style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginTop": "2px"})
                    ], style={"display": "inline-block", "marginRight": "2px"}))
                else:
                    components.append(trigger_element)
            elif args_list:
                # Arguments only: badges above, framed text below
                arg_badges = [
                    html.Span(
                        f"E{arg['event_num']}-Arg-{arg['label']}",
                        style={
                            "backgroundColor": arg["color"],
                            "fontSize": "0.65em",
                            "marginRight": "2px",
                            "marginBottom": "4px",
                            "display": "inline-block",
                            "color": "black",
                            "padding": "2px 6px",
                            "borderRadius": "12px",
                            "border": "none"
                        }
                    ) for arg in args_list
                ]
                
                # Use first argument's color for frame
                frame_color = args_list[0]["color"]
                
                components.append(html.Span([
                    html.Div(arg_badges, style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "2px"}),
                    html.Span(
                        source[start:end+1],
                        style={
                            "padding": "2px 4px",
                            "borderRadius": "3px",
                            "border": f"2px solid {frame_color}",
                            "display": "inline-block"
                        }
                    )
                ], style={"display": "inline-block", "marginRight": "2px"}))
            else:
                components.append(html.Span(source[start:end+1]))
            
            last_end = end + 1
        
        # Add remaining text
        if last_end < len(source):
            components.append(html.Span(source[last_end:]))
        
        return html.Div(
            components,
            style={
                "padding": "10px",
                "backgroundColor": "#f5f5f5",
                "borderRadius": "12px",
                "fontFamily": "monospace",
                "fontSize": "0.95em",
                "whiteSpace": "pre-wrap",
                "wordWrap": "break-word",
                "lineHeight": "2.5"
            }
        )
    
    # Create displays for each mode
    pipeline_events = ae_results_by_mode.get("pipeline", {}).get("events", [])
    e2e_events = ae_results_by_mode.get("e2e", {}).get("events", [])
    merged_events = ae_results_by_mode.get("merged", {}).get("events", [])
    
    pipeline_display = create_mode_combined_display("pipeline", pipeline_events)
    e2e_display = create_mode_combined_display("e2e", e2e_events)
    merged_display = create_mode_combined_display("merged", merged_events)
    
    # Return tabs with three modes
    return dbc.Tabs([
        dbc.Tab(label=f"Pipeline Mode ({len(pipeline_events)} events)", children=[
            html.Div(pipeline_display, className="mt-2")
        ]),
        dbc.Tab(label=f"E2E Mode ({len(e2e_events)} events)", children=[
            html.Div(e2e_display, className="mt-2")
        ]),
        dbc.Tab(label=f"Merged Mode ({len(merged_events)} events)", children=[
            html.Div(merged_display, className="mt-2")
        ])
    ])


def create_single_mode_combined_display(source: str, events: List[Dict]) -> html.Div:
    """Create display for a single mode with triggers and arguments."""
    if not source:
        return html.P("No source text", className="text-muted")

    EVENT_COLORS = ["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#ff99cc", "#c2c2f0"]

    def get_event_color(event_num):
        return EVENT_COLORS[(event_num - 1) % len(EVENT_COLORS)]

    if not events:
        return html.Div([
            html.Pre(source, style={
                "padding": "10px",
                "backgroundColor": "#f5f5f5",
                "borderRadius": "4px",
                "fontFamily": "monospace",
                "fontSize": "0.95em"
            })
        ])

    triggers_by_pos = {}
    arguments_by_pos = {}

    for event_idx, event in enumerate(events):
        event_num = event_idx + 1
        event_color = get_event_color(event_num)

        trigger = event.get("trigger", {})
        trigger_offset = trigger.get("offset", [])
        if trigger_offset and len(trigger_offset) == 2:
            start, end = trigger_offset[0], trigger_offset[1]
            triggers_by_pos.setdefault((start, end), []).append({
                "text": trigger.get("text", ""),
                "type": trigger.get("type", ""),
                "event_num": event_num,
                "color": event_color
            })

        for arg in event.get("arguments", []):
            arg_offset = arg.get("offset", [])
            if arg_offset and len(arg_offset) == 2:
                start, end = arg_offset[0], arg_offset[1]
                arguments_by_pos.setdefault((start, end), []).append({
                    "text": arg.get("text", ""),
                    "label": arg.get("role", ""),
                    "event_num": event_num,
                    "color": event_color
                })

    components = []
    last_end = 0
    all_positions = sorted(set(list(triggers_by_pos.keys()) + list(arguments_by_pos.keys())))

    for start, end in all_positions:
        if start > last_end:
            components.append(html.Span(source[last_end:start]))

        trigger_list = triggers_by_pos.get((start, end), [])
        args_list = arguments_by_pos.get((start, end), [])

        if trigger_list:
            trigger_badges = []
            for trigger_info in trigger_list:
                trigger_badges.append(
                    html.Span(
                        f"E{trigger_info['event_num']}-{trigger_info['type']}",
                        style={
                            "backgroundColor": trigger_info["color"],
                            "fontSize": "0.65em",
                            "marginLeft": "4px",
                            "display": "inline-block",
                            "color": "black",
                            "padding": "2px 6px",
                            "borderRadius": "12px",
                            "border": "none"
                        }
                    )
                )

            trigger_color = trigger_list[0]["color"]

            trigger_element = html.Span([
                html.Mark(
                    source[start:end+1],
                    style={
                        "backgroundColor": trigger_color,
                        "padding": "2px 4px",
                        "borderRadius": "3px",
                        "fontWeight": "bold",
                        "border": f"2px solid {trigger_color}"
                    }
                )
            ] + trigger_badges, style={"display": "inline-block", "marginRight": "2px", "whiteSpace": "nowrap"})

            if args_list:
                arg_badges = [
                    html.Span(
                        f"E{arg['event_num']}-Arg-{arg['label']}",
                        style={
                            "backgroundColor": arg["color"],
                            "fontSize": "0.65em",
                            "marginRight": "2px",
                            "display": "inline-block",
                            "color": "black",
                            "padding": "2px 6px",
                            "borderRadius": "12px",
                            "border": "none"
                        }
                    ) for arg in args_list
                ]

                components.append(html.Span([
                    trigger_element,
                    html.Br(),
                    html.Div(arg_badges, style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginTop": "2px"})
                ], style={"display": "inline-block", "marginRight": "2px"}))
            else:
                components.append(trigger_element)
        elif args_list:
            arg_badges = [
                html.Span(
                    f"E{arg['event_num']}-Arg-{arg['label']}",
                    style={
                        "backgroundColor": arg["color"],
                        "fontSize": "0.65em",
                        "marginRight": "2px",
                        "marginBottom": "4px",
                        "display": "inline-block",
                        "color": "black",
                        "padding": "2px 6px",
                        "borderRadius": "12px",
                        "border": "none"
                    }
                ) for arg in args_list
            ]

            frame_color = args_list[0]["color"]

            components.append(html.Span([
                html.Div(arg_badges, style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "2px"}),
                html.Span(
                    source[start:end+1],
                    style={
                        "padding": "2px 4px",
                        "borderRadius": "3px",
                        "border": f"2px solid {frame_color}",
                        "display": "inline-block"
                    }
                )
            ], style={"display": "inline-block", "marginRight": "2px"}))

        last_end = end + 1

    if last_end < len(source):
        components.append(html.Span(source[last_end:]))

    return html.Div(components, style={
        "padding": "10px",
        "backgroundColor": "#f5f5f5",
        "borderRadius": "4px",
        "lineHeight": "2.2",
        "fontFamily": "monospace"
    })


# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB], suppress_callback_exceptions=True)
app.title = "Cross-domain Event Extraction"

def create_navbar() -> dbc.Navbar:
    """Create a navbar for page navigation."""
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("", className="ms-2"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Introduction", href="/", active="exact")),
                dbc.NavItem(dbc.NavLink("Playground", href="/playground", active="exact")),
                dbc.NavItem(dbc.NavLink("Event Extraction", href="/app", active="exact")),
            ], className="ms-auto", navbar=True),
        ], fluid=True),
        color="light",
        dark=False,
        className="mb-4",
    )


def create_intro_layout() -> dbc.Container:
    """Create the introduction page."""
    def schema_tree(ds_key: str) -> html.Div:
        schema = patterns.get(ds_key, {})
        event_items = []
        for event_type, roles in schema.items():
            role_list = html.Ul([html.Li(role) for role in roles]) if roles else html.Div("No roles", className="text-muted")
            event_items.append(
                html.Li(
                    html.Details([
                        html.Summary(event_type),
                        role_list
                    ])
                )
            )
        return html.Div([
            html.P(f"{len(schema)} event types", className="text-muted"),
            html.Ul(event_items, className="mb-0"),
        ])

    def chunk_schemas(cols_per_row: int = 3) -> List[dbc.Row]:
        rows: List[dbc.Row] = []
        for i in range(0, len(DATASETS), cols_per_row):
            row_cols = []
            for ds in DATASETS[i:i + cols_per_row]:
                row_cols.append(
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader(html.H5(ds, className="mb-0")),
                            dbc.CardBody([
                                schema_tree(ds),
                            ], style={"maxHeight": "420px", "overflowY": "auto"}),
                        ], className="h-100"),
                        md=4,
                        className="mb-4",
                    )
                )
            rows.append(dbc.Row(row_cols, className="mb-2"))
        return rows

    schema_rows = chunk_schemas()

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("Cross-domain Event Extraction Application", className="mb-3 mt-2"),
                html.P(
                    "This interface supports two-stage event extraction with flexible pipeline and end-to-end modes. "
                            "You can annotate the same document with multiple datasets/schemas by re-uploading and selecting different datasets.",
                            className="mt-2 text-muted"
                        ),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Label("Features")),
                    dbc.CardBody([
                        html.Ul([
                            html.Li("File upload (JSON with document strings)"),
                            html.Li("Dataset/schema selection (geneva, wikievents, casie, genia2013, m2e2, rams)"),
                            html.Li("Model type selection (domain-specific or cross-domain)"),
                            html.Li("Event detection (pipeline, e2e, merged modes with highlighting)"),
                            html.Li("Argument extraction (with argument highlighting and roles)"),
                            html.Li("Multi-dataset annotation for same document"),
                            html.Li("Result saving with hierarchical dataset organization"),
                        ]),
                        
                    ])
                ], className="mb-3")
            ], md=7),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Label("Modes")),
                    dbc.CardBody([
                        html.Ul([
                            html.Li("Pipeline: Stage 1. Trigger Identification + Trigger Classification: Stage 2. Argument Extraction"),
                            html.Li("End-to-End: Trigger Classification directly from text"),
                            html.Li("Merged: Combine pipeline + end-to-end triggers for Stage 2"),
                            html.Li("Complete E2E: One-step trigger + argument extraction"),
                        ]),
                        dbc.Button("Go to Event Extraction", href="/app", color="primary", className="mt-2")
                    ])
                ])
            ], md=5)
        ]),
        html.H4("Current Available Dataset Schemas", className="mt-4 mb-2"),
        html.P("Expand each event type to view its argument roles."),
        *schema_rows,
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "paddingBottom": "30px"})


def create_playground_layout() -> dbc.Container:
    """Create a small playground for the example text."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Test the example text with different modes.", className="mb-3 mt-2"),
                html.Label("Input Text", className="fw-bold"),
                dcc.Textarea(
                    id="pg-input-text",
                    value=EXAMPLE_TEXT,
                    style={"width": "100%", "height": "50px"},
                    className="mb-3",
                ),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Label("Settings")),
                    dbc.CardBody([
                        html.Label("Dataset", className="fw-bold"),
                        dcc.Dropdown(
                            id="pg-dataset",
                            options=[{"label": ds, "value": ds} for ds in DATASETS],
                            value="geneva",
                            clearable=False,
                            className="mb-3",
                        ),
                        html.Label("Model Type", className="fw-bold"),
                        dcc.Dropdown(
                            id="pg-model-type",
                            options=[{"label": mt, "value": mt} for mt in MODEL_TYPES],
                            value="domain-specific",
                            clearable=False,
                            className="mb-3",
                        ),
                        dbc.Button("Run Event Detection", id="pg-run-detection", color="primary", className="w-100 mb-2"),
                        dbc.Button("Run Argument Extraction", id="pg-run-ae", color="success", className="w-100 mb-2", disabled=True),
                        dbc.Button("Run Complete E2E", id="pg-run-e2e", color="info", className="w-100"),
                        dcc.Store(id="pg-detection-store"),
                    ])
                ])
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Label("Event Detection Output")),
                    dbc.CardBody(html.Div(id="pg-detection-results", className="small"))
                ]),
                dbc.Card([
                    dbc.CardHeader(html.Label("Argument Extraction Output")),
                    dbc.CardBody(html.Div(id="pg-ae-results", className="small"))
                ]),
                dbc.Card([
                    dbc.CardHeader(html.Label("Complete E2E Output")),
                    dbc.CardBody(html.Div(id="pg-e2e-results", className="small"))
                ])
            ], md=10)
        ])
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "paddingBottom": "30px"})


def create_extraction_layout() -> dbc.Container:
    """Create the main event extraction layout."""
    return dbc.Container([

        # Store components for state management
        dcc.Store(id='uploaded-data-store'),
        dcc.Store(id='current-document-store'),
        dcc.Store(id='event-detection-results-store'),
        dcc.Store(id='complete-e2e-results-store'),
        dcc.Store(id='all-results-store'),
        dcc.Store(id='detection-progress-store', data=0),
        dcc.Store(id='extraction-progress-store', data=0),
        dcc.Store(id='detection-running', data=False),
        dcc.Store(id='extraction-running', data=False),
        dcc.Download(id='download-results'),

        # Interval components for progress updates
        dcc.Interval(id='detection-interval', interval=500, n_intervals=0, disabled=True),
        dcc.Interval(id='extraction-interval', interval=500, n_intervals=0, disabled=True),

        # File Upload Section
        dbc.Card(
            dbc.CardBody([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        "Drag and Drop or ",
                        html.A("Select Files"),
                        " (JSON with 'documents' array containing 'id' and 'text' fields)"
                    ]),
                    style={
                        'width': '100%',
                        'height': '30px',
                        'lineHeight': '30px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False
                ),
                html.Div(id='upload-status', className="mt-2")
            ]),
            className="mb-2"
        ),

        # Document Selection Section
        dbc.Card([
            dbc.CardHeader(
                dbc.Row([
                    dbc.Col([
                        html.Strong("Select a document")
                    ], md=2),
                    dbc.Col([
                        dcc.Dropdown(id='document-selector', placeholder="Select a document...", disabled=True)
                    ], md=8),
                    dbc.Col([
                        dbc.Button(
                            "Next",
                            id='next-document-btn',
                            color="secondary",
                            className="w-100",
                            disabled=True
                        )
                    ], md=2)
                ], className="g-2 align-items-center")
            ),
            dbc.CardBody([
                html.Div(id='document-display', className="mt-3")
            ])
        ], className="mb-2"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Strong("Two-Stage Event Extraction (Pipeline)")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(
                                        dbc.Row([
                                            dbc.Col([
                                                html.Strong("Stage 1: ")
                                            ], md=2),
                                            dbc.Col([
                                                dcc.Dropdown(
                                                    id='dataset-selector',
                                                    options=[{"label": ds, "value": ds} for ds in DATASETS],
                                                    placeholder="Dataset",
                                                    disabled=True
                                                )
                                            ], md=2),
                                            dbc.Col([
                                                dcc.Dropdown(
                                                    id='model-type-selector-stage1',
                                                    options=[{"label": mt, "value": mt} for mt in MODEL_TYPES],
                                                    value="domain-specific",
                                                    placeholder="Model type",
                                                    disabled=True
                                                )
                                            ], md=4),
                                            dbc.Col([
                                                dbc.Button(
                                                    "Run Event Detection",
                                                    id='run-detection-btn',
                                                    color="primary",
                                                    disabled=True,
                                                    className="w-100"
                                                )
                                            ], md=4)
                                        ], className="g-2 align-items-center")
                                    ),
                                    dbc.CardBody([
                                        dbc.Progress(
                                            id='detection-progress',
                                            value=0,
                                            min=0,
                                            max=100,
                                            style={"display": "none"}
                                        ),
                                        html.Div(id='detection-status', className="text-center"),
                                        html.Div(id='detection-progress-text', className="text-center small text-muted", style={"marginTop": "5px"}),
                                        html.Div(id='detection-results', className="mt-3")
                                    ])
                                ], className="h-100"),
                            ], md=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(
                                        dbc.Row([
                                            dbc.Col([
                                                html.Strong("Stage 2:")
                                            ], md=2),
                                            dbc.Col([
                                                dcc.Dropdown(
                                                    id='model-type-selector-stage2',
                                                    options=[{"label": mt, "value": mt} for mt in MODEL_TYPES],
                                                    value="cross-domain",
                                                    placeholder="Model type",
                                                    disabled=True
                                                )
                                            ], md=4),
                                            dbc.Col([
                                                dbc.Button(
                                                    "Run Event Arguments Extraction",
                                                    id='validate-detection-btn',
                                                    color="success",
                                                    disabled=True,
                                                    className="w-100"
                                                )
                                            ], md=6)
                                        ], className="g-2 align-items-center")
                                    ),
                                    dbc.CardBody([
                                        html.Div([
                                            dbc.Progress(
                                                id='extraction-progress',
                                                value=10,
                                                min=0,
                                                max=100,
                                                color="success",
                                            ),
                                            html.Div(id='extraction-progress-text', className="text-left small text-muted", style={"marginTop": "5px"})
                                        ], style={"marginTop": "10px"}),
                                        html.Div(id='argument-extraction-results', className="mt-3", style={"display": "none"}),
                                    ])
                                ], className="h-100"),
                            ], md=6),
                        ], className="g-2")
                        ,
                        html.Div(id='validation-message', className="mt-2")
                    ])
                ], className="mb-2"),
            ], md=12)
        ], className="mb-2"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        dbc.Row([
                            dbc.Col([
                                html.Strong("Complete Event Extraction (End-to-End)")
                            ], md=3),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='e2e-dataset-selector',
                                    options=[{"label": ds, "value": ds} for ds in DATASETS],
                                    placeholder="Dataset",
                                    disabled=True
                                )
                            ], md=3),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='model-type-selector-e2e',
                                    options=[{"label": mt, "value": mt} for mt in MODEL_TYPES],
                                    value="cross-domain",
                                    placeholder="Model type",
                                    disabled=True
                                )
                            ], md=3),
                            dbc.Col([
                                dbc.Button(
                                    "Run Complete E2E",
                                    id='run-complete-e2e-btn',
                                    color="info",
                                    disabled=True,
                                    className="w-100"
                                )
                            ], md=3)
                        ], className="g-2 align-items-center")
                    ),
                    dbc.CardBody([
                        html.Div(id='complete-e2e-status', className="text-center"),
                        html.Div(id='complete-e2e-results', className="mt-2", style={"display": "none"}),
                    ])
                ], className="mb-2"),
            ], md=12)
        ], className="mb-2"),

        dbc.Row([
            dbc.Col([
                html.Div(id='save-button-container', className="mt-3")
            ])
        ])

    ], fluid=True, style={"backgroundColor": "#f8f9fa", "paddingBottom": "30px"})


# App layout
app.layout = html.Div([
    dcc.Location(id="url"),
    create_navbar(),
    html.Div(id="page-content")
])


@callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: Optional[str]):
    if pathname in ("/", "/intro", None):
        return create_intro_layout()
    if pathname in ("/playground", "/pg"):
        return create_playground_layout()
    if pathname in ("/app", "/extract", "/extraction"):
        return create_extraction_layout()
    return dbc.Container([
        html.H2("Page not found", className="mt-4"),
        html.P("Return to the introduction page."),
        dbc.Button("Go to Introduction", href="/", color="secondary")
    ], fluid=True)


@callback(
    Output("pg-detection-store", "data"),
    Output("pg-detection-results", "children"),
    Input("pg-run-detection", "n_clicks"),
    State("pg-dataset", "value"),
    State("pg-model-type", "value"),
    State("pg-input-text", "value"),
)
def run_playground_detection(n_clicks, dataset, model_type, input_text):
    if not n_clicks:
        raise PreventUpdate

    if not input_text:
        return None, dbc.Alert("Please enter input text.", color="warning")

    tokenizer_dir, model_dir = get_model_path(model_type, dataset)
    model, tokenizer = model_cache.get_model(model_type, tokenizer_dir, model_dir)

    event_detection_item = run_single_inference_event_detection(
        doc_id="playground",
        tokenizer=tokenizer,
        model=model,
        ds_key=dataset,
        plain_text=input_text,
    )
    parsed_results = parse_and_merge_single_inference_event_detection_results(event_detection_item)

    # Filter triggers with valid offsets
    def filter_valid_triggers(triggers):
        valid_triggers = []
        for trigger_tuple in triggers:
            if isinstance(trigger_tuple, (list, tuple)) and len(trigger_tuple) >= 3:
                text, event_type, offset = trigger_tuple[0], trigger_tuple[1], trigger_tuple[2]
                if offset and isinstance(offset, (list, tuple)) and len(offset) == 2:
                    valid_triggers.append(trigger_tuple)
        return valid_triggers

    tc_pipeline = filter_valid_triggers(parsed_results.get("trigger_classification_pipeline", []))
    tc_e2e = filter_valid_triggers(parsed_results.get("trigger_classification_e2e", []))
    tc_merged = filter_valid_triggers(parsed_results.get("trigger_classification_merged", []))

    parsed_results["trigger_classification_pipeline"] = tc_pipeline
    parsed_results["trigger_classification_e2e"] = tc_e2e
    parsed_results["trigger_classification_merged"] = tc_merged

    def format_triggers(triggers, mode_name):
        if not triggers:
            return html.P(f"No triggers detected in {mode_name}", className="text-muted")
        items = []
        for i, (text, event_type, offset) in enumerate(triggers):
            items.append(
                html.Div([
                    dbc.Badge(f"E{i + 1}", color="secondary", className="me-2"),
                    dbc.Badge(event_type, color="primary", className="me-2"),
                    html.Span(f'"{text}"', className="fw-bold"),
                    html.Small(f" {offset}", className="text-muted ms-2")
                ], className="mb-2")
            )
        return html.Div(items)

    source_display = create_source_display(
        input_text,
        {
            "pipeline": tc_pipeline,
            "e2e": tc_e2e,
            "merged": tc_merged,
        }
    )

    results_display = html.Div([
        dbc.Card([
            dbc.CardHeader(html.H6("Annotated Source Text", className="mb-0")),
            dbc.CardBody(source_display)
        ], className="mb-3"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6(f"Pipeline Mode ({len(tc_pipeline)} triggers)", className="mb-0")),
                            dbc.CardBody([format_triggers(tc_pipeline, "Pipeline Mode")])
                        ])
                    ], md=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6(f"E2E Mode ({len(tc_e2e)} triggers)", className="mb-0")),
                            dbc.CardBody([format_triggers(tc_e2e, "E2E Mode")])
                        ])
                    ], md=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6(f"Merged Mode ({len(tc_merged)} triggers)", className="mb-0")),
                            dbc.CardBody([format_triggers(tc_merged, "Merged Mode")])
                        ])
                    ], md=4),
                ])
            ])
        ])
    ])

    payload = {
        "event_detection_item": event_detection_item,
        "parsed_results": parsed_results,
        "dataset": dataset,
        "model_type": model_type,
        "source": input_text,
    }
    return payload, results_display


@callback(
    Output("pg-run-ae", "disabled"),
    Input("pg-detection-store", "data"),
)
def enable_playground_ae(detection_data):
    return not bool(detection_data)


@callback(
    Output("pg-ae-results", "children"),
    Input("pg-run-ae", "n_clicks"),
    State("pg-detection-store", "data"),
    State("pg-dataset", "value"),
    State("pg-model-type", "value"),
    State("pg-input-text", "value"),
)
def run_playground_ae(n_clicks, detection_data, dataset, model_type, input_text):
    if not n_clicks or not detection_data:
        raise PreventUpdate

    if not input_text:
        return dbc.Alert("Please enter input text.", color="warning")

    tokenizer_dir, model_dir = get_model_path(model_type, dataset)
    model, tokenizer = model_cache.get_model(model_type, tokenizer_dir, model_dir)

    parsed_results = detection_data.get("parsed_results", {})
    ae_item = run_single_inference_event_argument_extraction(
        tokenizer=tokenizer,
        model=model,
        ds_key=dataset,
        plain_text=input_text,
        event_detection_item={
            "trigger_classification_pipeline": parsed_results.get("trigger_classification_pipeline", []),
            "trigger_classification_e2e": parsed_results.get("trigger_classification_e2e", []),
            "trigger_classification_merged": parsed_results.get("trigger_classification_merged", []),
        },
    )

    ae_results_by_mode = {}
    for mode, trigger_key, ae_key in [
        ("pipeline", "trigger_classification_pipeline", "argument_extraction_pipeline_pipeline"),
        ("e2e", "trigger_classification_e2e", "argument_extraction_pipeline_e2e"),
        ("merged", "trigger_classification_merged", "argument_extraction_pipeline_merged"),
    ]:
        triggers = parsed_results.get(trigger_key, [])
        if not triggers:
            ae_results_by_mode[mode] = {"events": []}
            continue
        structured = structure_argument_extraction_pipeline_predictions(
            ae_item,
            triggers,
            ae_key
        )
        ae_results_by_mode[mode] = structured

    combined_display = dbc.Card([
        dbc.CardHeader(html.H6("Combined Annotation View (Triggers + Arguments)", className="mb-0")),
        dbc.CardBody([
            create_combined_annotation_display(input_text, ae_results_by_mode)
        ])
    ], className="mb-3")

    pipeline_events = ae_results_by_mode["pipeline"].get("events", [])
    e2e_events = ae_results_by_mode["e2e"].get("events", [])
    merged_events = ae_results_by_mode["merged"].get("events", [])

    pipeline_cards = [create_event_card(event, f"Event {i+1}") for i, event in enumerate(pipeline_events)]
    e2e_cards = [create_event_card(event, f"Event {i+1}") for i, event in enumerate(e2e_events)]
    merged_cards = [create_event_card(event, f"Event {i+1}") for i, event in enumerate(merged_events)]

    event_cards_display = dbc.Card([
        dbc.CardHeader(html.H6("Event Details", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6(f"Pipeline Mode ({len(pipeline_events)} events)", className="mb-0")),
                        dbc.CardBody([
                            html.Div(pipeline_cards) if pipeline_cards else html.P("No events", className="text-muted")
                        ])
                    ])
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6(f"E2E Mode ({len(e2e_events)} events)", className="mb-0")),
                        dbc.CardBody([
                            html.Div(e2e_cards) if e2e_cards else html.P("No events", className="text-muted")
                        ])
                    ])
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6(f"Merged Mode ({len(merged_events)} events)", className="mb-0")),
                        dbc.CardBody([
                            html.Div(merged_cards) if merged_cards else html.P("No events", className="text-muted")
                        ])
                    ])
                ], md=4),
            ])
        ])
    ])

    results_display = html.Div([
        combined_display,
        event_cards_display
    ])

    return results_display


@callback(
    Output("pg-e2e-results", "children"),
    Input("pg-run-e2e", "n_clicks"),
    State("pg-dataset", "value"),
    State("pg-model-type", "value"),
    State("pg-input-text", "value"),
)
def run_playground_e2e(n_clicks, dataset, model_type, input_text):
    if not n_clicks:
        raise PreventUpdate

    if not input_text:
        return dbc.Alert("Please enter input text.", color="warning")

    tokenizer_dir, model_dir = get_model_path(model_type, dataset)
    model, tokenizer = model_cache.get_model(model_type, tokenizer_dir, model_dir)
    e2e_item = run_single_inference_event_extraction_e2e(
        doc_id="playground",
        tokenizer=tokenizer,
        model=model,
        ds_key=dataset,
        plain_text=input_text,
    )
    structured = present_parsed_output(e2e_item)

    e2e_events = structured.get("events", [])

    combined_display = dbc.Card([
        dbc.CardHeader(html.H6("Combined Annotation View (Triggers + Arguments)", className="mb-0")),
        dbc.CardBody([
            create_single_mode_combined_display(input_text, e2e_events)
        ])
    ], className="mb-3")

    e2e_cards = [create_event_card(event, f"Event {i+1}") for i, event in enumerate(e2e_events)]
    event_cards_display = dbc.Card([
        dbc.CardHeader(html.H6(f"E2E Mode ({len(e2e_events)} events)", className="mb-0")),
        dbc.CardBody([
            html.Div(e2e_cards) if e2e_cards else html.P("No events", className="text-muted")
        ])
    ])

    return html.Div([
        combined_display,
        event_cards_display
    ])


# Callback: Handle file upload
@callback(
    Output('uploaded-data-store', 'data'),
    Output('upload-status', 'children'),
    Output('dataset-selector', 'disabled'),
    Output('model-type-selector-stage1', 'disabled'),
    Output('model-type-selector-stage2', 'disabled'),
    Output('e2e-dataset-selector', 'disabled'),
    Output('model-type-selector-e2e', 'disabled'),
    Output('document-selector', 'disabled'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
)
def handle_file_upload(contents, filename):
    if not contents:
        raise PreventUpdate
    
    try:
        # Parse JSON content from base64-encoded upload
        content_string = contents.split(',')[1] if ',' in contents else contents
        decoded = base64.b64decode(content_string)
        text_content = decoded.decode('utf-8')
        
        # Try parsing as single JSON first, then as JSONL if that fails
        data = None
        try:
            data = json.loads(text_content)
        except json.JSONDecodeError:
            # Try JSONL format (one JSON object per line)
            documents = []
            for i, line in enumerate(text_content.strip().split('\n')):
                if line.strip():
                    documents.append(json.loads(line))
            data = {"documents": documents}
        
        # Validate structure
        if 'documents' not in data:
            return None, dbc.Alert("Error: JSON must contain 'documents' key", color="danger"), True, True, True, True, True, True
        
        documents = data['documents']
        if not documents or not isinstance(documents, list):
            return None, dbc.Alert("Error: 'documents' must be a non-empty list", color="danger"), True, True, True, True, True, True
        
        # Validate document structure - normalize 'id' and 'doc_id'
        for i, doc in enumerate(documents):
            if 'id' not in doc and 'doc_id' not in doc:
                # Auto-assign ID if missing
                doc['id'] = f"doc_{i}"
            elif 'doc_id' in doc and 'id' not in doc:
                # Rename doc_id to id for consistency
                doc['id'] = doc.pop('doc_id')
            
            if 'text' not in doc:
                return None, dbc.Alert("Error: Each document must have 'text' field", color="danger"), True, True, True, True, True, True
        
        status = dbc.Alert(f"Loaded {len(documents)} documents from {filename}", color="success")
        return data, status, False, False, False, False, False, False
        
    except Exception as e:
        return None, dbc.Alert(f"Error: {str(e)}", color="danger"), True, True, True, True, True, True


# Callback: Update document selector
@callback(
    Output('document-selector', 'options'),
    Output('document-selector', 'value'),
    Input('uploaded-data-store', 'data'),
)
def update_document_selector(data):
    if not data:
        raise PreventUpdate
    
    documents = data.get('documents', [])
    options = []
    for i, doc in enumerate(documents):
        doc_id = doc.get('id', f"doc_{i}")
        text_preview = doc.get('text', 'N/A')[:50]
        options.append({"label": f"Doc {doc_id}: {text_preview}...", "value": i})
    
    return options, 0 if options else None


@callback(
    Output('next-document-btn', 'disabled'),
    Input('document-selector', 'value'),
    State('uploaded-data-store', 'data'),
)
def toggle_next_document_button(selected_idx, data):
    if not data:
        return True
    documents = data.get('documents', [])
    if not documents or selected_idx is None:
        return True
    return selected_idx >= len(documents) - 1


@callback(
    Output('document-selector', 'value', allow_duplicate=True),
    Output('event-detection-results-store', 'data', allow_duplicate=True),
    Output('detection-results', 'children', allow_duplicate=True),
    Output('detection-status', 'children', allow_duplicate=True),
    Output('validate-detection-btn', 'disabled', allow_duplicate=True),
    Output('argument-extraction-results', 'children', allow_duplicate=True),
    Output('argument-extraction-results', 'style', allow_duplicate=True),
    Output('complete-e2e-results-store', 'data', allow_duplicate=True),
    Output('complete-e2e-results', 'children', allow_duplicate=True),
    Output('complete-e2e-results', 'style', allow_duplicate=True),
    Output('complete-e2e-status', 'children', allow_duplicate=True),
    Output('save-button-container', 'children', allow_duplicate=True),
    Output('validation-message', 'children', allow_duplicate=True),
    Output('detection-progress-store', 'data', allow_duplicate=True),
    Output('extraction-progress-store', 'data', allow_duplicate=True),
    Output('detection-running', 'data', allow_duplicate=True),
    Output('extraction-running', 'data', allow_duplicate=True),
    Input('next-document-btn', 'n_clicks'),
    State('document-selector', 'value'),
    State('uploaded-data-store', 'data'),
    prevent_initial_call=True,
)
def go_to_next_document(n_clicks, selected_idx, data):
    if not n_clicks or not data:
        raise PreventUpdate
    documents = data.get('documents', [])
    if selected_idx is None or not documents:
        raise PreventUpdate
    next_idx = min(selected_idx + 1, len(documents) - 1)
    if next_idx == selected_idx:
        raise PreventUpdate
    return (
        next_idx,
        None,
        None,
        None,
        True,
        None,
        {"display": "none"},
        None,
        None,
        {"display": "none"},
        None,
        None,
        None,
        0,
        0,
        False,
        False,
    )


# Callback: Display selected document
@callback(
    Output('document-display', 'children'),
    Output('current-document-store', 'data'),
    Input('document-selector', 'value'),
    State('uploaded-data-store', 'data'),
    Input('event-detection-results-store', 'data'),
)
def display_selected_document(selected_idx, data, detection_results):
    if selected_idx is None or not data:
        raise PreventUpdate
    
    documents = data.get('documents', [])
    if selected_idx >= len(documents):
        raise PreventUpdate
    
    doc = documents[selected_idx]
    
    # If detection results are available, show annotated text
    if detection_results:
        parsed_results = detection_results.get('parsed_results', {})
        tc_pipeline = parsed_results.get("trigger_classification_pipeline", [])
        tc_e2e = parsed_results.get("trigger_classification_e2e", [])
        tc_merged = parsed_results.get("trigger_classification_merged", [])

        combined_results = detection_results.get('argument_extraction_results')
        if combined_results:
            source_display = create_combined_annotation_display(doc['text'], combined_results)
            source_title = "Combined Annotation View (Triggers + Arguments)"
        else:
            source_display = create_source_display(
                doc['text'],
                {
                    "pipeline": tc_pipeline,
                    "e2e": tc_e2e,
                    "merged": tc_merged
                }
            )
            source_title = "Annotated Source Text"
        
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Label(f"Document ID: {doc.get('id', 'N/A')}"),
                    html.Div([
                        html.Label(f"{source_title}:", style={"marginTop": "15px", "display": "block"}),
                        source_display
                    ], style={"marginTop": "10px"})
                ])
            ])
        ]), doc
    
    # Show plain text if no detection results
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Label(f"Document ID: {doc.get('id', 'N/A')}"),
                html.Div(doc['text'], style={
                    "marginTop": "10px",
                    "padding": "10px",
                    "backgroundColor": "#f5f5f5",
                    "borderRadius": "4px",
                    "lineHeight": "1.8"
                })
            ])
        ])
    ]), doc


# Callback: Enable run detection button
@callback(
    Output('run-detection-btn', 'disabled'),
    Input('current-document-store', 'data'),
    Input('dataset-selector', 'value'),
    Input('model-type-selector-stage1', 'value'),
)
def enable_detection_button(current_doc, dataset, model_type):
    if current_doc and dataset and model_type:
        return False
    return True


@callback(
    Output('run-complete-e2e-btn', 'disabled'),
    Input('current-document-store', 'data'),
    Input('e2e-dataset-selector', 'value'),
    Input('model-type-selector-e2e', 'value'),
)
def enable_complete_e2e_button(current_doc, dataset, model_type):
    if current_doc and dataset and model_type:
        return False
    return True


# Callback: Clear results when dataset or model type changes
@callback(
    Output('event-detection-results-store', 'data', allow_duplicate=True),
    Output('detection-results', 'children', allow_duplicate=True),
    Output('detection-status', 'children', allow_duplicate=True),
    Output('validate-detection-btn', 'disabled', allow_duplicate=True),
    Output('argument-extraction-results', 'children', allow_duplicate=True),
    Output('argument-extraction-results', 'style', allow_duplicate=True),
    Output('validation-message', 'children', allow_duplicate=True),
    Input('dataset-selector', 'value'),
    Input('model-type-selector-stage1', 'value'),
    prevent_initial_call=True,
)
def clear_results_on_config_change(dataset, model_type):
    """Clear detection and extraction results when dataset or model type changes."""
    return (
        None,  # Clear event-detection-results-store
        None,  # Clear detection-results
        None,  # Clear detection-status
        True,  # Disable validate-detection-btn
        None,  # Clear argument-extraction-results
        {"display": "none"},  # Hide argument-extraction-results
        None  # Clear validation-message
    )


@callback(
    Output('complete-e2e-results-store', 'data', allow_duplicate=True),
    Output('complete-e2e-results', 'children', allow_duplicate=True),
    Output('complete-e2e-results', 'style', allow_duplicate=True),
    Output('complete-e2e-status', 'children', allow_duplicate=True),
    Input('e2e-dataset-selector', 'value'),
    Input('model-type-selector-e2e', 'value'),
    Input('current-document-store', 'data'),
    prevent_initial_call=True,
)
def clear_complete_e2e_on_change(dataset, model_type, current_doc):
    """Clear complete E2E results when configuration or document changes."""
    return None, None, {"display": "none"}, None


# Callback: Generate dynamic save button with document and dataset info
@callback(
    Output('save-button-container', 'children'),
    Input('current-document-store', 'data'),
    Input('dataset-selector', 'value'),
    Input('argument-extraction-results', 'style'),
    Input('complete-e2e-results-store', 'data'),
    prevent_initial_call=True,
)
def update_save_button(current_doc, dataset, ae_results_style, complete_e2e_data):
    """Generate save button with dynamic label showing document ID and dataset."""
    if not current_doc:
        return None
    
    doc_id = current_doc.get('id', 'unknown')
    is_extraction_complete = ae_results_style.get("display") == "block" if isinstance(ae_results_style, dict) else False
    has_complete_e2e = bool(complete_e2e_data)

    label_lines = ["Save Results", f"Document: {doc_id}"]
    if dataset:
        label_lines.append(f"Stage1/2 Schema: {dataset}")
    e2e_dataset = complete_e2e_data.get("dataset") if isinstance(complete_e2e_data, dict) else None
    if e2e_dataset:
        label_lines.append(f"Complete E2E Schema: {e2e_dataset}")

    button_label = "\n".join(label_lines)
    
    return dbc.Button(
        button_label,
        id='save-results-btn',
        color="info",
        disabled=not (is_extraction_complete or has_complete_e2e),
        className="w-100",
        style={"whiteSpace": "pre-wrap", "fontSize": "0.85em"}
    )


# Callback: Update detection progress bar
@callback(
    Output('detection-progress', 'value'),
    Output('detection-progress', 'label'),
    Output('detection-progress', 'style'),
    Output('detection-interval', 'disabled'),
    Input('detection-interval', 'n_intervals'),
    State('detection-running', 'data'),
    State('detection-progress-store', 'data'),
)
def update_detection_progress(n, is_running, final_progress):
    if not is_running:
        return final_progress, f"{final_progress}%" if final_progress >= 5 else "", {"display": "none" if final_progress == 0 else "block"}, True
    
    # Simulate progress (max 90% while running, final 100% set by main callback)
    progress = min((n * 5) % 95, 90)
    return progress, f"{progress}%" if progress >= 5 else "", {"display": "block"}, False


# Callback: Start detection interval
@callback(
    Output('detection-running', 'data', allow_duplicate=True),
    Output('detection-interval', 'n_intervals'),
    Input('run-detection-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def start_detection_interval(n):
    if n is None:
        raise PreventUpdate
    return True, 0


# Callback: Update extraction progress bar
@callback(
    Output('extraction-progress', 'value'),
    Output('extraction-progress', 'label'),
    Output('extraction-progress', 'style'),
    Output('extraction-interval', 'disabled'),
    Input('extraction-interval', 'n_intervals'),
    State('extraction-running', 'data'),
    State('extraction-progress-store', 'data'),
)
def update_extraction_progress(n, is_running, final_progress):
    if not is_running:
        return final_progress, f"{final_progress}%" if final_progress >= 5 else "", {"display": "none" if final_progress == 0 else "block"}, True
    
    # Simulate progress (max 90% while running, final 100% set by main callback)
    progress = min((n * 5) % 95, 90)
    return progress, f"{progress}%" if progress >= 5 else "", {"display": "block"}, False


# Callback: Start extraction interval
@callback(
    Output('extraction-running', 'data', allow_duplicate=True),
    Output('extraction-interval', 'n_intervals'),
    Input('validate-detection-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def start_extraction_interval(n):
    if n is None:
        raise PreventUpdate
    return True, 0


# Callback: Stop detection interval when complete
@callback(
    Output('detection-running', 'data', allow_duplicate=True),
    Input('detection-progress-store', 'data'),
    prevent_initial_call=True,
)
def stop_detection_interval(progress):
    if progress == 100:
        return False
    raise PreventUpdate


# Callback: Stop extraction interval when complete
@callback(
    Output('extraction-running', 'data', allow_duplicate=True),
    Input('extraction-progress-store', 'data'),
    prevent_initial_call=True,
)
def stop_extraction_interval(progress):
    if progress == 100:
        return False
    raise PreventUpdate


# Callback: Run event detection
@callback(
    Output('event-detection-results-store', 'data'),
    Output('detection-results', 'children'),
    Output('detection-status', 'children'),
    Output('validate-detection-btn', 'disabled'),
    Output('save-button-container', 'children', allow_duplicate=True),
    Output('detection-progress-store', 'data'),
    Input('run-detection-btn', 'n_clicks'),
    State('current-document-store', 'data'),
    State('dataset-selector', 'value'),
    State('model-type-selector-stage1', 'value'),
    prevent_initial_call=True,
)
def run_event_detection(n_clicks, current_doc, dataset, model_type):
    if n_clicks is None or not current_doc or not dataset or not model_type:
        raise PreventUpdate
    
    try:
        # Start progress interval
        detection_status = dbc.Spinner(html.Div("Running event detection..."), color="primary")
        
        # Get model
        tokenizer_dir, model_dir = get_model_path(model_type, dataset)
        
        # Check if local model path exists
        model_path_error = validate_model_path(model_dir)
        if model_path_error:
            error_msg = dbc.Alert(model_path_error, color="danger")
            return None, error_msg, dbc.Alert("Model not found", color="danger"), True, None, 0
        
        model, tokenizer = model_cache.get_model(model_type, tokenizer_dir, model_dir)
        
        # Run event detection
        event_detection_item = run_single_inference_event_detection(
            doc_id=current_doc['id'],
            tokenizer=tokenizer,
            model=model,
            ds_key=dataset,
            plain_text=current_doc['text'],
            max_length=512,
        )
        
        # Parse and merge results
        parsed_results = parse_and_merge_single_inference_event_detection_results(event_detection_item)
        
        # Filter out triggers with empty or invalid offsets
        def filter_valid_triggers(triggers):
            """Keep only triggers that have valid offsets found in text."""
            valid_triggers = []
            for trigger_tuple in triggers:
                if isinstance(trigger_tuple, (list, tuple)) and len(trigger_tuple) >= 3:
                    text, event_type, offset = trigger_tuple[0], trigger_tuple[1], trigger_tuple[2]
                    # Only keep if offset exists and has 2 elements [start, end]
                    if offset and isinstance(offset, (list, tuple)) and len(offset) == 2:
                        valid_triggers.append(trigger_tuple)
            return valid_triggers
        
        # Create display with three tabs
        tc_pipeline = filter_valid_triggers(parsed_results.get("trigger_classification_pipeline", []))
        tc_e2e = filter_valid_triggers(parsed_results.get("trigger_classification_e2e", []))
        tc_merged = filter_valid_triggers(parsed_results.get("trigger_classification_merged", []))
        
        # Update parsed_results with filtered triggers
        parsed_results["trigger_classification_pipeline"] = tc_pipeline
        parsed_results["trigger_classification_e2e"] = tc_e2e
        parsed_results["trigger_classification_merged"] = tc_merged
        
        # Create trigger lists for each mode
        def format_triggers(triggers, mode_name):
            if not triggers:
                return html.P(f"No triggers detected in {mode_name}", className="text-muted")
            items = []
            for i, (text, event_type, offset) in enumerate(triggers):
                items.append(
                    html.Div([
                        dbc.Badge(f"E{i + 1}", color="secondary", className="me-2"),
                        dbc.Badge(event_type, color="primary", className="me-2"),
                        html.Span(f'"{text}"', className="fw-bold"),
                        html.Small(f" {offset}", className="text-muted ms-2")
                    ], className="mb-2")
                )
            return html.Div(items)
        
        results_display = dbc.Card([
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(
                        label=f"Pipeline Mode ({len(tc_pipeline)} triggers)",
                        children=[html.Div(format_triggers(tc_pipeline, "Pipeline Mode"), className="mt-2")]
                    ),
                    dbc.Tab(
                        label=f"E2E Mode ({len(tc_e2e)} triggers)",
                        children=[html.Div(format_triggers(tc_e2e, "E2E Mode"), className="mt-2")]
                    ),
                    dbc.Tab(
                        label=f"Merged Mode ({len(tc_merged)} triggers)",
                        children=[html.Div(format_triggers(tc_merged, "Merged Mode"), className="mt-2")]
                    ),
                ])
            ])
        ])
        
        status = dbc.Alert("Event detection completed", color="success", className="p-2", style={"fontSize": "0.85em", "marginBottom": "0"})
        
        # Store results for argument extraction
        stored_results = {
            "parsed_results": json.loads(json.dumps(parsed_results, default=str)),
            "event_detection_item": json.loads(json.dumps(event_detection_item, default=str)),
            "dataset": dataset,
            "model_type": model_type,
            "doc_id": current_doc['id'],
            "source": current_doc['text']
        }
        
        # Generate button with document info
        doc_id = current_doc.get('id', 'unknown')
        button_label = f"Save Results\nDocument: {doc_id}\nSchema: {dataset}"
        save_button = dbc.Button(
            button_label,
            id='save-results-btn',
            color="info",
            disabled=True,  # Disabled until argument extraction is complete
            className="w-100",
            style={"whiteSpace": "pre-wrap", "fontSize": "0.85em"}
        )
        
        return stored_results, results_display, status, False, save_button, 100
        
    except Exception as e:
        error_msg = dbc.Alert(f"Error: {str(e)}\n{traceback.format_exc()}", color="danger")
        print(f"Error in event detection: {traceback.format_exc()}")
        return None, error_msg, dbc.Alert("Error occurred", color="danger"), True, None, 0


# Callback: Run argument extraction
@callback(
    Output('event-detection-results-store', 'data', allow_duplicate=True),
    Output('argument-extraction-results', 'style'),
    Output('argument-extraction-results', 'children'),
    Output('validation-message', 'children'),
    Output('extraction-progress-store', 'data'),
    Input('validate-detection-btn', 'n_clicks'),
    State('event-detection-results-store', 'data'),
    State('current-document-store', 'data'),
    State('dataset-selector', 'value'),
    State('model-type-selector-stage2', 'value'),
    prevent_initial_call=True,
)
def run_argument_extraction(n_clicks, detection_results, current_doc, dataset, model_type):
    if n_clicks is None or not detection_results or not current_doc:
        raise PreventUpdate
    
    try:
        # Get model
        tokenizer_dir, model_dir = get_model_path(model_type, dataset)
        model, tokenizer = model_cache.get_model(model_type, tokenizer_dir, model_dir)
        
        parsed_results = detection_results['parsed_results']
        
        # Prepare parsed event detection for AE input
        parsed_event_detection = {
            "trigger_classification_pipeline": parsed_results.get("trigger_classification_pipeline", []),
            "trigger_classification_e2e": parsed_results.get("trigger_classification_e2e", []),
            "trigger_classification_merged": parsed_results.get("trigger_classification_merged", []),
        }
        
        # Run argument extraction
        argument_extraction_item = run_single_inference_event_argument_extraction(
            tokenizer=tokenizer,
            model=model,
            ds_key=dataset,
            plain_text=current_doc['text'],
            event_detection_item=parsed_event_detection,
            max_length=512,
        )
        
        # Parse argument extraction results for each mode
        ae_results_by_mode = {}
        
        for mode, trigger_key, ae_key in [
            ("pipeline", "trigger_classification_pipeline", "argument_extraction_pipeline_pipeline"),
            ("e2e", "trigger_classification_e2e", "argument_extraction_pipeline_e2e"),
            ("merged", "trigger_classification_merged", "argument_extraction_pipeline_merged"),
        ]:
            triggers = parsed_results.get(trigger_key, [])
            if not triggers:
                ae_results_by_mode[mode] = {"events": []}
                continue
            
            structured = structure_argument_extraction_pipeline_predictions(
                argument_extraction_item,
                triggers,
                ae_key
            )
            ae_results_by_mode[mode] = structured
        
        # Create display with columns for event cards
        pipeline_events = ae_results_by_mode["pipeline"].get("events", [])
        e2e_events = ae_results_by_mode["e2e"].get("events", [])
        merged_events = ae_results_by_mode["merged"].get("events", [])
        
        # Create event cards for each mode
        pipeline_cards = [create_event_card(event, f"Event {i+1}") for i, event in enumerate(pipeline_events)]
        e2e_cards = [create_event_card(event, f"Event {i+1}") for i, event in enumerate(e2e_events)]
        merged_cards = [create_event_card(event, f"Event {i+1}") for i, event in enumerate(merged_events)]
        
        event_cards_display = dbc.Card([
            dbc.CardHeader(html.H6("Event Details", className="mb-0")),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(
                        label=f"Pipeline Mode ({len(pipeline_events)} events)",
                        children=[
                            html.Div(pipeline_cards, className="mt-2") if pipeline_cards else html.P("No events", className="text-muted mt-2")
                        ]
                    ),
                    dbc.Tab(
                        label=f"E2E Mode ({len(e2e_events)} events)",
                        children=[
                            html.Div(e2e_cards, className="mt-2") if e2e_cards else html.P("No events", className="text-muted mt-2")
                        ]
                    ),
                    dbc.Tab(
                        label=f"Merged Mode ({len(merged_events)} events)",
                        children=[
                            html.Div(merged_cards, className="mt-2") if merged_cards else html.P("No events", className="text-muted mt-2")
                        ]
                    ),
                ])
            ])
        ])
        
        results_display = html.Div([event_cards_display])
        
        # Store results
        detection_results['argument_extraction_results'] = ae_results_by_mode
        
        validation_msg = dbc.Alert([
            html.Strong("Argument extraction completed"),
            html.Br(),
            "Results are ready to save. Click 'Save Results' button."
        ], color="success", className="p-2", style={"fontSize": "0.85em", "marginBottom": "0"})
        
        return detection_results, {"display": "block"}, results_display, validation_msg, 100
        
    except Exception as e:
        error_msg = dbc.Alert(f"Error: {str(e)}\n{traceback.format_exc()}", color="danger")
        print(f"Error in argument extraction: {traceback.format_exc()}")
        return detection_results, {"display": "none"}, error_msg, error_msg, 0


# Callback: Run complete end-to-end event extraction
@callback(
    Output('complete-e2e-results-store', 'data'),
    Output('complete-e2e-results', 'children'),
    Output('complete-e2e-results', 'style'),
    Output('complete-e2e-status', 'children'),
    Input('run-complete-e2e-btn', 'n_clicks'),
    State('current-document-store', 'data'),
    State('e2e-dataset-selector', 'value'),
    State('model-type-selector-e2e', 'value'),
    prevent_initial_call=True,
)
def run_complete_e2e(n_clicks, current_doc, dataset, model_type):
    if n_clicks is None or not current_doc or not dataset or not model_type:
        raise PreventUpdate

    try:
        tokenizer_dir, model_dir = get_model_path(model_type, dataset)
        model_path_error = validate_model_path(model_dir)
        if model_path_error:
            error_msg = dbc.Alert(model_path_error, color="danger")
            return None, None, {"display": "none"}, error_msg

        model, tokenizer = model_cache.get_model(model_type, tokenizer_dir, model_dir)
        e2e_item = run_single_inference_event_extraction_e2e(
            doc_id=current_doc['id'],
            tokenizer=tokenizer,
            model=model,
            ds_key=dataset,
            plain_text=current_doc['text'],
            max_length=512,
        )
        structured = present_parsed_output(e2e_item)
        e2e_events = structured.get("events", [])

        combined_display = dbc.Card([
            dbc.CardHeader(html.H6("Combined Annotation View (Triggers + Arguments)", className="mb-0")),
            dbc.CardBody([
                create_single_mode_combined_display(current_doc['text'], e2e_events)
            ])
        ], className="mb-3")

        e2e_cards = [create_event_card(event, f"Event {i + 1}") for i, event in enumerate(e2e_events)]
        event_cards_display = dbc.Card([
            dbc.CardHeader(html.H6(f"Complete E2E ({len(e2e_events)} events)", className="mb-0")),
            dbc.CardBody([
                html.Div(e2e_cards) if e2e_cards else html.P("No events", className="text-muted")
            ])
        ])

        results_display = html.Div([
            combined_display,
            event_cards_display
        ])

        status = dbc.Alert("Complete E2E extraction completed", color="success", className="p-2", style={"fontSize": "0.85em", "marginBottom": "0"})
        stored_results = {
            "dataset": dataset,
            "model_type": model_type,
            "doc_id": current_doc['id'],
            "source": current_doc['text'],
            "complete_e2e_results": structured
        }

        return stored_results, results_display, {"display": "block"}, status

    except Exception as e:
        error_msg = dbc.Alert(f"Error: {str(e)}\n{traceback.format_exc()}", color="danger")
        print(f"Error in complete e2e extraction: {traceback.format_exc()}")
        return None, None, {"display": "none"}, error_msg


# Callback: Save and switch dataset
# Callback: Save results (unified)
@callback(
    Output('all-results-store', 'data'),
    Output('validation-message', 'children', allow_duplicate=True),
    Output('download-results', 'data'),
    Input('save-results-btn', 'n_clicks'),
    State('all-results-store', 'data'),
    State('event-detection-results-store', 'data'),
    State('complete-e2e-results-store', 'data'),
    State('dataset-selector', 'value'),
    State('current-document-store', 'data'),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def save_results(n_clicks, all_results, current_results, complete_e2e_results, current_dataset, current_doc):
    if n_clicks is None:
        raise PreventUpdate
    
    try:
        has_ae = bool(current_results and 'argument_extraction_results' in current_results)
        has_complete_e2e = bool(complete_e2e_results and complete_e2e_results.get('complete_e2e_results'))

        if not has_ae and not has_complete_e2e:
            error_msg = dbc.Alert([
                html.Strong("Cannot save without results"),
                html.Br(),
                "Please run Stage 2 or Complete E2E before saving."
            ], color="warning")
            return all_results, error_msg, dash.no_update
        
        base_doc_id = None
        base_source = None
        if current_results:
            base_doc_id = current_results.get('doc_id')
            base_source = current_results.get('source')
        if complete_e2e_results:
            base_doc_id = base_doc_id or complete_e2e_results.get('doc_id')
            base_source = base_source or complete_e2e_results.get('source')

        if not base_doc_id or not base_source:
            error_msg = dbc.Alert("Error: Missing document context for saving.", color="danger")
            return all_results, error_msg, dash.no_update

        # Initialize all_results if needed
        if not all_results:
            all_results = {
                "doc_id": base_doc_id,
                "source": base_source,
                "events": {},
                "complete_e2e": {}
            }
        else:
            all_results.setdefault("events", {})
            all_results.setdefault("complete_e2e", {})
        
        # Save current results to all_results under the dataset key
        if has_ae:
            ae_results = current_results['argument_extraction_results']
            all_results['events'][current_dataset] = ae_results

        if has_complete_e2e:
            e2e_dataset = complete_e2e_results.get('dataset', 'unknown')
            all_results['complete_e2e'][e2e_dataset] = complete_e2e_results['complete_e2e_results']
        
        download_filename = f"annotated_{all_results['doc_id']}.json"
        download_payload = json.dumps(all_results, indent=2)
        
        doc_id = all_results.get('doc_id', 'Unknown')
        datasets_saved = list(all_results['events'].keys())
        e2e_saved = list(all_results.get('complete_e2e', {}).keys())
        validation_msg = dbc.Alert([
            html.Strong("Results saved"),
            html.Br(),
            html.Div(f"Document: {doc_id}", className="text-muted small"),
            html.Div(f"Schemas saved (Stage 1/2): {', '.join(datasets_saved)}", className="text-muted small"),
            html.Div(f"Schemas saved (Complete E2E): {', '.join(e2e_saved)}", className="text-muted small"),
            html.Div(f"Download: {download_filename}", className="text-muted small")
        ], color="success")
        
        return all_results, validation_msg, dcc.send_string(download_payload, filename=download_filename)
        
    except Exception as e:
        error_msg = dbc.Alert(f"Error: {str(e)}", color="danger")
        return all_results, error_msg, dash.no_update


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050, dev_tools_hot_reload=False,
        use_reloader=False)
