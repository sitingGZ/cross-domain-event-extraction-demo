"""User-centric dashboard for inspecting event extraction results.

This dashboard does not call `infer.py` directly. Instead it talks to the REST
API exposed by `web_api_dash_app.py` and focuses on document-level review,
aggregated statistics, schema coverage, and mode comparisons.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import dash
from dash import Input, Output, State, callback, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go


API_BASE_URL = os.environ.get("EVENT_API_BASE_URL", "http://127.0.0.1:8051").rstrip("/")
DEFAULT_TEXT = "Argentina rejects reports that it has transferred uranium enrichment techniques to Iran (2958)."
DEFAULT_DATASET = "geneva"
DEFAULT_MODEL_TYPE = "domain-specific"
DEFAULT_MODES = ["pipeline", "e2e", "merged"]
DEFAULT_PANELS = [
    "overview",
    "documents",
    "event_structures",
    "trigger_stats",
    "event_type_distribution",
    "argument_text_distribution",
    "argument_role_distribution",
    "schema_overview",
]


def _api_request(path: str, payload: Optional[Dict[str, Any]] = None, method: str = "POST") -> Dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    body = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if method == "GET":
        if payload:
            query = urllib.parse.urlencode(payload, doseq=True)
            url = f"{url}?{query}"
        request = urllib.request.Request(url, headers=headers, method="GET")
    else:
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")

    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def _safe_get(record: Dict[str, Any], keys: Sequence[str], default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _normalize_records(payload: Any) -> List[Dict[str, Any]]:
    if payload is None:
        return []

    if isinstance(payload, list):
        normalized: List[Dict[str, Any]] = []
        for index, item in enumerate(payload):
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append({"doc_id": f"doc-{index + 1}", "text": item})
        return normalized

    if isinstance(payload, dict):
        for key in ("documents", "docs", "data", "records", "items"):
            if isinstance(payload.get(key), list):
                return _normalize_records(payload.get(key))

        if any(key in payload for key in ("text", "source", "content", "document")):
            return [payload]

        normalized = []
        for index, (key, value) in enumerate(payload.items()):
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("doc_id", key)
                normalized.append(item)
            else:
                normalized.append({"doc_id": key, "text": value})
        return normalized

    return []


def _decode_upload(contents: str) -> Any:
    _, encoded = contents.split(",", 1)
    decoded = base64.b64decode(encoded)
    text = decoded.decode("utf-8")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        index = 0
        values = []

        while index < len(text):
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text):
                break

            value, next_index = decoder.raw_decode(text, index)
            values.append(value)
            index = next_index

        if values:
            return values

        raise


def _sample_records() -> List[Dict[str, Any]]:
    return [
        {
            "doc_id": "sample-1",
            "text": DEFAULT_TEXT,
            "dataset": DEFAULT_DATASET,
            "model_type": DEFAULT_MODEL_TYPE,
        },
        {
            "doc_id": "sample-2",
            "text": "The committee announced sanctions after the meeting ended.",
            "dataset": "wikievents",
            "model_type": "cross-domain",
        },
    ]


def _record_text(record: Dict[str, Any]) -> str:
    return _safe_get(record, ("text", "source", "content", "document", "sentence"), default="")


def _record_doc_id(record: Dict[str, Any], index: int) -> str:
    return _safe_get(record, ("doc_id", "id", "document_id", "uid", "name"), default=f"doc-{index + 1}")


def _record_dataset(record: Dict[str, Any], default: str) -> str:
    return _safe_get(record, ("dataset", "domain", "ds_key"), default=default)


def _record_model_type(record: Dict[str, Any], default: str) -> str:
    return _safe_get(record, ("model_type", "model", "mode"), default=default)


def _result_key(doc_id: str, dataset: str, model_type: str, source: str) -> str:
    source_marker = " ".join(source.split())[:80]
    return f"{doc_id}::{dataset}::{model_type}::{source_marker}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_inference_results(record: Dict[str, Any]) -> bool:
    return any(key in record for key in ("event_detection_item", "parsed_detection", "parsed_argument_extractions", "event_extraction_item", "parsed_event_extraction"))


def _infer_record(record: Dict[str, Any], default_dataset: str, default_model_type: str, max_length: int) -> Dict[str, Any]:
    text = _record_text(record)
    if not text:
        doc_id = _record_doc_id(record, 0)
        dataset = _record_dataset(record, default_dataset)
        model_type = _record_model_type(record, default_model_type)
        return {
            "doc_id": doc_id,
            "dataset": dataset,
            "model_type": model_type,
            "source": "",
            "result_key": _result_key(doc_id, dataset, model_type, ""),
            "analyzed_at": _utc_now_iso(),
        }

    if _has_inference_results(record):
        normalized = dict(record)
        doc_id = normalized.setdefault("doc_id", _record_doc_id(record, 0))
        dataset = normalized.setdefault("dataset", _record_dataset(record, default_dataset))
        model_type = normalized.setdefault("model_type", _record_model_type(record, default_model_type))
        normalized.setdefault("source", text)
        normalized.setdefault("result_key", _result_key(doc_id, dataset, model_type, text))
        normalized.setdefault("analyzed_at", _utc_now_iso())
        return normalized

    dataset = _record_dataset(record, default_dataset)
    model_type = _record_model_type(record, default_model_type)
    doc_id = _record_doc_id(record, 0)

    response = _api_request(
        "/api/infer",
        {
            "dataset": dataset,
            "model_type": model_type,
            "doc_id": doc_id,
            "text": text,
            "max_length": max_length,
        },
        method="POST",
    )
    response.setdefault("dataset", dataset)
    response.setdefault("model_type", model_type)
    response.setdefault("doc_id", doc_id)
    response.setdefault("source", text)
    response.setdefault("result_key", _result_key(doc_id, dataset, model_type, text))
    response.setdefault("analyzed_at", _utc_now_iso())
    return response


def _select_modes(result: Dict[str, Any], selected_modes: Sequence[str]) -> List[str]:
    if not selected_modes:
        return list(DEFAULT_MODES)
    return [mode for mode in selected_modes if mode in result.get("detection", {}).get("parsed_detection", {}) or mode in DEFAULT_MODES]


def _extract_events(result: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
    parsed_argument_extractions = result.get("arguments", {}).get("parsed_argument_extractions", {})
    mode_payload = parsed_argument_extractions.get(mode, {})
    return mode_payload.get("events", []) if isinstance(mode_payload, dict) else []


def _trigger_sequences(result: Dict[str, Any], mode: str) -> List[Tuple[str, str, List[int]]]:
    parsed_detection = result.get("detection", {}).get("parsed_detection", {})
    if mode == "pipeline":
        return parsed_detection.get("trigger_classification_pipeline", [])
    if mode == "e2e":
        return parsed_detection.get("trigger_classification_e2e", [])
    if mode == "merged":
        return parsed_detection.get("trigger_classification_merged", [])
    return []


def _count_events(events: Iterable[Dict[str, Any]], event_type_filter: Sequence[str], role_filter: Sequence[str]) -> Tuple[Counter, Counter, Counter, Counter, Counter]:
    trigger_counter: Counter = Counter()
    event_type_counter: Counter = Counter()
    role_counter: Counter = Counter()
    trigger_word_counter: Counter = Counter()
    argument_text_counter: Counter = Counter()

    for event in events:
        trigger = event.get("trigger", {}) if isinstance(event, dict) else {}
        trigger_text = str(trigger.get("text", "")).strip()
        trigger_type = str(trigger.get("type", "")).strip()

        if event_type_filter and trigger_type not in event_type_filter:
            continue

        if trigger_text:
            trigger_counter[trigger_text] += 1
            trigger_word_counter[trigger_text.lower()] += 1
        if trigger_type:
            event_type_counter[trigger_type] += 1

        for argument in event.get("arguments", []):
            role = str(argument.get("role", "")).strip()
            arg_text = str(argument.get("text", "")).strip()
            if role_filter and role not in role_filter:
                continue
            if role:
                role_counter[role] += 1
            if arg_text:
                argument_text_counter[arg_text] += 1

    return trigger_counter, event_type_counter, role_counter, trigger_word_counter, argument_text_counter


def _figure_from_counter(title: str, counter: Counter, color: str) -> go.Figure:
    figure = go.Figure()
    if counter:
        labels = list(counter.keys())[:15]
        values = [counter[label] for label in labels]
        figure.add_trace(go.Bar(x=labels, y=values, marker_color=color))
        figure.update_layout(
            title=title,
            margin=dict(l=20, r=20, t=50, b=20),
            height=320,
            xaxis_title="",
            yaxis_title="Count",
        )
    else:
        figure.update_layout(
            title=title,
            margin=dict(l=20, r=20, t=50, b=20),
            height=320,
        )
        figure.add_annotation(text="No data for current selection", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
    return figure


def _build_kpi(title: str, value: Any, subtitle: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Div(title, className="text-uppercase text-muted small"),
            html.H3(str(value), className="mb-1"),
            html.Div(subtitle, className="small text-muted"),
        ]),
        className="h-100 shadow-sm",
    )


def _format_offset(offset: Any) -> str:
    if isinstance(offset, (list, tuple)) and len(offset) == 2:
        return f"[{offset[0]}, {offset[1]}]"
    return "[]"


def _event_cards(result: Dict[str, Any], selected_modes: Sequence[str], event_type_filter: Sequence[str], role_filter: Sequence[str]) -> List[html.Div]:
    cards: List[html.Div] = []
    source = result.get("source", "")

    for mode in selected_modes:
        events = _extract_events(result, mode)
        if not events:
            continue

        filtered_events = []
        for event in events:
            trigger = event.get("trigger", {})
            trigger_type = str(trigger.get("type", "")).strip()
            if event_type_filter and trigger_type not in event_type_filter:
                continue

            filtered_arguments = []
            for argument in event.get("arguments", []):
                role = str(argument.get("role", "")).strip()
                if role_filter and role not in role_filter:
                    continue
                filtered_arguments.append(argument)

            cloned_event = dict(event)
            cloned_event["arguments"] = filtered_arguments
            filtered_events.append(cloned_event)

        if not filtered_events:
            continue

        mode_cards = []
        for index, event in enumerate(filtered_events):
            trigger = event.get("trigger", {})
            arguments = event.get("arguments", [])
            mode_cards.append(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            dbc.Badge(f"E{index + 1}", color="secondary", className="me-2"),
                            dbc.Badge(mode.upper(), color="primary", className="me-2"),
                            html.Span(trigger.get("type", "Unknown"), className="fw-semibold"),
                        ], className="mb-2"),
                        html.Div([
                            html.Strong("Trigger: "),
                            html.Span(trigger.get("text", "")),
                            html.Small(f" {_format_offset(trigger.get('offset', []))}", className="text-muted ms-2"),
                        ], className="mb-2"),
                        html.Div(
                            [
                                html.Strong("Arguments"),
                                html.Ul(
                                    [
                                        html.Li([
                                            html.Span(f"{argument.get('role', 'Role')}: ", className="fw-semibold"),
                                            html.Span(argument.get("text", "")),
                                            html.Small(f" {_format_offset(argument.get('offset', []))}", className="text-muted ms-2"),
                                        ])
                                        for argument in arguments
                                    ]
                                ) if arguments else html.P("No arguments in current filter.", className="text-muted mb-0"),
                            ]
                        ),
                    ]),
                    className="mb-3 shadow-sm",
                )
            )

        cards.append(
            dbc.AccordionItem(
                [
                    html.P(source, className="text-muted small mb-3"),
                    html.Div(mode_cards),
                ],
                title=f"{result.get('doc_id', 'document')} - {mode.upper()} ({len(filtered_events)} events)",
            )
        )

    return cards


def _render_schema_overview(results: Sequence[Dict[str, Any]]) -> html.Div:
    schema_counter = Counter()
    by_dataset: Dict[str, Counter] = defaultdict(Counter)

    for result in results:
        dataset = str(result.get("dataset", DEFAULT_DATASET))
        model_type = str(result.get("model_type", DEFAULT_MODEL_TYPE))
        schema_counter[(dataset, model_type)] += 1
        by_dataset[dataset][model_type] += 1

    cards = []
    for (dataset, model_type), count in schema_counter.most_common():
        cards.append(
            dbc.Card(
                dbc.CardBody([
                    html.Div(dataset, className="fw-semibold"),
                    html.Div(model_type, className="text-muted small"),
                    html.H4(count, className="mt-2 mb-0"),
                ]),
                className="shadow-sm",
            )
        )

    if not cards:
        return html.P("No schema information available.", className="text-muted")

    return html.Div([
        dbc.Row([dbc.Col(card, md=4, className="mb-3") for card in cards]),
    ])


def _render_documents_table(results: Sequence[Dict[str, Any]], selected_modes: Sequence[str], event_type_filter: Sequence[str], role_filter: Sequence[str]) -> dash_table.DataTable:
    rows = []
    for result in results:
        result_key = result.get("result_key", "")
        doc_id = result.get("doc_id", "")
        dataset = result.get("dataset", DEFAULT_DATASET)
        model_type = result.get("model_type", DEFAULT_MODEL_TYPE)
        analyzed_at = result.get("analyzed_at", "")
        mode_event_counts = {}

        for mode in selected_modes:
            events = _extract_events(result, mode)
            if event_type_filter:
                events = [event for event in events if str(event.get("trigger", {}).get("type", "")).strip() in event_type_filter]
            if role_filter:
                filtered_events = []
                for event in events:
                    event_copy = dict(event)
                    event_copy["arguments"] = [argument for argument in event.get("arguments", []) if str(argument.get("role", "")).strip() in role_filter]
                    if event_copy["arguments"] or not role_filter:
                        filtered_events.append(event_copy)
                events = filtered_events
            mode_event_counts[mode] = len(events)

        rows.append(
            {
                "result_key": result_key,
                "doc_id": doc_id,
                "dataset": dataset,
                "model_type": model_type,
                "analyzed_at": analyzed_at,
                "source_preview": str(result.get("source", ""))[:120],
                "pipeline_events": mode_event_counts.get("pipeline", 0),
                "e2e_events": mode_event_counts.get("e2e", 0),
                "merged_events": mode_event_counts.get("merged", 0),
            }
        )

    return dash_table.DataTable(
        columns=[
            {"name": "Run Key", "id": "result_key"},
            {"name": "Document ID", "id": "doc_id"},
            {"name": "Dataset", "id": "dataset"},
            {"name": "Model Type", "id": "model_type"},
            {"name": "Analyzed At", "id": "analyzed_at"},
            {"name": "Source Preview", "id": "source_preview"},
            {"name": "Pipeline", "id": "pipeline_events"},
            {"name": "E2E", "id": "e2e_events"},
            {"name": "Merged", "id": "merged_events"},
        ],
        data=rows,
        page_size=10,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_cell={"padding": "10px", "fontFamily": "system-ui", "fontSize": "0.92rem"},
        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "700"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#fcfcfd"},
        ],
    )


def _merge_analysis_runs(existing: Sequence[Dict[str, Any]], new_runs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}

    for item in existing:
        if isinstance(item, dict):
            key = str(item.get("result_key") or _result_key(
                str(item.get("doc_id", "")),
                str(item.get("dataset", DEFAULT_DATASET)),
                str(item.get("model_type", DEFAULT_MODEL_TYPE)),
                str(item.get("source", "")),
            ))
            merged[key] = dict(item)

    for item in new_runs:
        if isinstance(item, dict):
            key = str(item.get("result_key") or _result_key(
                str(item.get("doc_id", "")),
                str(item.get("dataset", DEFAULT_DATASET)),
                str(item.get("model_type", DEFAULT_MODEL_TYPE)),
                str(item.get("source", "")),
            ))
            merged[key] = dict(item)

    return list(merged.values())


def _build_layout() -> dbc.Container:
    return dbc.Container(
        [
            dcc.Store(id="insights-records-store"),
            dcc.Store(id="insights-results-store"),
            dcc.Store(id="insights-filter-store"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Div("Event Extraction Insights", className="display-6 fw-semibold"),
                                    html.P(
                                        "Upload documents, run API-backed extraction, and inspect event structures, trigger words, event types, argument roles, and schema coverage.",
                                        className="text-muted mb-0",
                                    ),
                                ],
                                className="mb-4",
                            ),
                            dbc.Alert(
                                [
                                    html.Strong("API: "),
                                    html.Span(API_BASE_URL),
                                    html.Span(". Start the REST bridge first, then use this page for review and filtering."),
                                ],
                                color="info",
                                className="shadow-sm",
                            ),
                        ],
                        md=8,
                    ),
                    dbc.Col(
                        _build_kpi("Status", "Ready", "Connect an upload or type text to begin."),
                        md=4,
                    ),
                ],
                className="mt-4 mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H5("User Controls", className="mb-0")),
                                    dbc.CardBody(
                                        [
                                            html.Label("API Base URL", className="fw-semibold"),
                                            dcc.Input(
                                                id="insights-api-base",
                                                type="text",
                                                value=API_BASE_URL,
                                                className="form-control mb-3",
                                            ),
                                            html.Label("Load documents", className="fw-semibold"),
                                            dcc.Upload(
                                                id="insights-upload",
                                                children=html.Div(["Drag and drop or ", html.A("select a JSON file")]),
                                                accept=".json",
                                                multiple=False,
                                                className="border rounded p-3 mb-2 text-center bg-light",
                                            ),
                                            html.Div(
                                                "Step 1: upload the JSON file. Step 2: choose the dataset/domain and model type to rerun extraction on the same documents.",
                                                className="small text-muted mb-3",
                                            ),
                                            html.Label("Default dataset / domain", className="fw-semibold"),
                                            dcc.Dropdown(
                                                id="insights-default-dataset",
                                                options=[{"label": ds, "value": ds} for ds in ["geneva", "wikievents", "casie", "genia2013", "m2e2", "rams", "cross-domain"]],
                                                value=DEFAULT_DATASET,
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            html.Label("Model type", className="fw-semibold"),
                                            dcc.Dropdown(
                                                id="insights-model-type",
                                                options=[
                                                    {"label": "domain-specific", "value": "domain-specific"},
                                                    {"label": "cross-domain", "value": "cross-domain"},
                                                ],
                                                value=DEFAULT_MODEL_TYPE,
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            dbc.Button("Load sample", id="insights-load-sample", color="secondary", outline=True, className="me-2 mb-3"),
                                            html.Div(id="insights-upload-status", className="small text-muted mb-3"),
                                            html.Label("Quick text input", className="fw-semibold"),
                                            dcc.Textarea(
                                                id="insights-input-text",
                                                value=DEFAULT_TEXT,
                                                style={"width": "100%", "minHeight": "120px"},
                                                className="mb-3",
                                            ),
                                            html.Label("Max docs to analyze", className="fw-semibold"),
                                            dcc.Input(
                                                id="insights-max-docs",
                                                type="number",
                                                min=1,
                                                max=100,
                                                value=10,
                                                className="form-control mb-3",
                                            ),
                                            html.Label("Show modes", className="fw-semibold"),
                                            dcc.Checklist(
                                                id="insights-modes",
                                                options=[
                                                    {"label": "Pipeline", "value": "pipeline"},
                                                    {"label": "E2E", "value": "e2e"},
                                                    {"label": "Merged", "value": "merged"},
                                                ],
                                                value=list(DEFAULT_MODES),
                                                inline=True,
                                                className="mb-3",
                                            ),
                                            html.Label("Panels to display", className="fw-semibold"),
                                            dcc.Checklist(
                                                id="insights-panels",
                                                options=[
                                                    {"label": "Overview", "value": "overview"},
                                                    {"label": "Documents", "value": "documents"},
                                                    {"label": "Event structures", "value": "event_structures"},
                                                    {"label": "Trigger stats", "value": "trigger_stats"},
                                                    {"label": "Event type distribution", "value": "event_type_distribution"},
                                                    {"label": "Argument text distribution", "value": "argument_text_distribution"},
                                                    {"label": "Argument role distribution", "value": "argument_role_distribution"},
                                                    {"label": "Schema overview", "value": "schema_overview"},
                                                ],
                                                value=list(DEFAULT_PANELS),
                                                className="mb-3",
                                            ),
                                            html.Label("Document filter", className="fw-semibold"),
                                            dcc.Dropdown(
                                                id="insights-doc-filter",
                                                options=[],
                                                multi=True,
                                                placeholder="Select documents to focus on",
                                                className="mb-3",
                                            ),
                                            html.Label("Event type filter", className="fw-semibold"),
                                            dcc.Dropdown(
                                                id="insights-event-type-filter",
                                                options=[],
                                                multi=True,
                                                placeholder="Filter by event type",
                                                className="mb-3",
                                            ),
                                            html.Label("Argument role filter", className="fw-semibold"),
                                            dcc.Dropdown(
                                                id="insights-role-filter",
                                                options=[],
                                                multi=True,
                                                placeholder="Filter by argument role",
                                                className="mb-3",
                                            ),
                                            dbc.Button("Analyze documents", id="insights-analyze", color="primary", className="w-100"),
                                        ]
                                    ),
                                ],
                                className="shadow-sm",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Alert(id="insights-status", color="light", className="shadow-sm"),
                            html.Div(id="insights-output"),
                        ],
                        md=8,
                    ),
                ]
            ),
        ],
        fluid=True,
        className="py-3",
    )


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB], suppress_callback_exceptions=True)
app.title = "Event Extraction Insights"
app.layout = _build_layout()
server = app.server


@callback(
    Output("insights-records-store", "data"),
    Output("insights-upload-status", "children"),
    Input("insights-upload", "contents"),
    State("insights-upload", "filename"),
    prevent_initial_call=True,
)
def cache_uploaded_records(contents: Optional[str], filename: Optional[str]):
    if not contents:
        raise PreventUpdate

    try:
        payload = _decode_upload(contents)
        records = _normalize_records(payload)
        if not records:
            return [], dbc.Alert(f"{filename or 'Upload'} did not contain any documents.", color="warning")
        return records, dbc.Alert(f"Loaded {len(records)} documents from {filename or 'upload' }.", color="success")
    except Exception as exc:  # pragma: no cover - shown to user
        return [], dbc.Alert(f"Could not read upload: {exc}", color="danger")


@callback(
    Output("insights-records-store", "data", allow_duplicate=True),
    Output("insights-upload-status", "children", allow_duplicate=True),
    Input("insights-load-sample", "n_clicks"),
    prevent_initial_call=True,
)
def load_sample_records(n_clicks: int):
    if not n_clicks:
        raise PreventUpdate
    sample = _sample_records()
    return sample, dbc.Alert(f"Loaded {len(sample)} sample documents.", color="secondary")


@callback(
    Output("insights-results-store", "data"),
    Output("insights-status", "children"),
    Output("insights-doc-filter", "options"),
    Output("insights-doc-filter", "value"),
    Output("insights-event-type-filter", "options"),
    Output("insights-event-type-filter", "value"),
    Output("insights-role-filter", "options"),
    Output("insights-role-filter", "value"),
    Input("insights-analyze", "n_clicks"),
    State("insights-records-store", "data"),
    State("insights-input-text", "value"),
    State("insights-default-dataset", "value"),
    State("insights-model-type", "value"),
    State("insights-max-docs", "value"),
    State("insights-api-base", "value"),
    State("insights-results-store", "data"),
    prevent_initial_call=True,
)
def analyze_documents(
    n_clicks: int,
    records: Optional[List[Dict[str, Any]]],
    fallback_text: Optional[str],
    default_dataset: str,
    model_type: str,
    max_docs: Optional[int],
    api_base_url: Optional[str],
    existing_results: Optional[List[Dict[str, Any]]],
):
    if not n_clicks:
        raise PreventUpdate

    global API_BASE_URL
    if api_base_url:
        API_BASE_URL = api_base_url.rstrip("/")

    base_records = records or []
    if not base_records and fallback_text:
        base_records = [{"doc_id": "input-text", "text": fallback_text, "dataset": default_dataset, "model_type": model_type}]

    if not base_records:
        return [], dbc.Alert("Upload a JSON file or type text before analyzing.", color="warning"), [], [], [], [], [], []

    limit = max(1, int(max_docs or 10))
    analysis_results: List[Dict[str, Any]] = []
    doc_options = []
    event_type_counter: Counter = Counter()
    role_counter: Counter = Counter()

    for index, record in enumerate(base_records[:limit]):
        record_for_run = {
            "doc_id": _record_doc_id(record, index),
            "text": _record_text(record),
        }
        normalized = _infer_record(record_for_run, default_dataset, model_type, max_length=512)
        normalized.setdefault("doc_id", record_for_run["doc_id"])
        normalized["dataset"] = default_dataset
        normalized["model_type"] = model_type
        normalized.setdefault("source", record_for_run["text"])
        analysis_results.append(normalized)
        doc_options.append({"label": normalized["doc_id"], "value": normalized["doc_id"]})

        for mode in DEFAULT_MODES:
            events = _extract_events(normalized, mode)
            for event in events:
                trigger = event.get("trigger", {})
                trigger_type = str(trigger.get("type", "")).strip()
                if trigger_type:
                    event_type_counter[trigger_type] += 1
                for argument in event.get("arguments", []):
                    role = str(argument.get("role", "")).strip()
                    if role:
                        role_counter[role] += 1

    if not analysis_results:
        return [], dbc.Alert("No records were analyzed.", color="warning"), [], [], [], [], [], []

    merged_results = _merge_analysis_runs(existing_results or [], analysis_results)

    full_event_types: Counter = Counter()
    full_roles: Counter = Counter()
    for result in merged_results:
        for mode in DEFAULT_MODES:
            events = _extract_events(result, mode)
            for event in events:
                trigger = event.get("trigger", {})
                trigger_type = str(trigger.get("type", "")).strip()
                if trigger_type:
                    full_event_types[trigger_type] += 1
                for argument in event.get("arguments", []):
                    role = str(argument.get("role", "")).strip()
                    if role:
                        full_roles[role] += 1

    event_type_options = [{"label": label, "value": label} for label in sorted(full_event_types)]
    role_options = [{"label": label, "value": label} for label in sorted(full_roles)]

    doc_options = [
        {
            "label": f"{item.get('doc_id', 'doc')} | {item.get('dataset', DEFAULT_DATASET)} | {item.get('model_type', DEFAULT_MODEL_TYPE)} | {item.get('analyzed_at', '')}",
            "value": item.get("result_key", item.get("doc_id", "")),
        }
        for item in merged_results
    ]

    return (
        merged_results,
        dbc.Alert(
            f"Saved {len(analysis_results)} new analysis run(s); {len(merged_results)} total run(s) are now stored using {API_BASE_URL}.",
            color="success",
        ),
        doc_options,
        [option["value"] for option in doc_options[-len(analysis_results):]] if analysis_results else [option["value"] for option in doc_options],
        event_type_options,
        [],
        role_options,
        [],
    )


@callback(
    Output("insights-output", "children"),
    Input("insights-results-store", "data"),
    Input("insights-doc-filter", "value"),
    Input("insights-event-type-filter", "value"),
    Input("insights-role-filter", "value"),
    Input("insights-modes", "value"),
    Input("insights-panels", "value"),
)
def render_dashboard(
    results: Optional[List[Dict[str, Any]]],
    selected_docs: Optional[List[str]],
    event_type_filter: Optional[List[str]],
    role_filter: Optional[List[str]],
    selected_modes: Optional[List[str]],
    selected_panels: Optional[List[str]],
):
    if not results:
        return dbc.Alert("Use the controls to upload documents and generate extraction summaries.", color="light")

    selected_modes = list(selected_modes or DEFAULT_MODES)
    selected_panels = list(selected_panels or DEFAULT_PANELS)
    selected_docs = set(selected_docs or [result.get("result_key") for result in results])
    event_type_filter = list(event_type_filter or [])
    role_filter = list(role_filter or [])

    visible_results = [result for result in results if result.get("result_key") in selected_docs]
    if not visible_results:
        visible_results = list(results)

    combined_events = []
    for result in visible_results:
        for mode in selected_modes:
            combined_events.extend(_extract_events(result, mode))

    trigger_counter, event_type_counter, role_counter, trigger_word_counter, argument_text_counter = _count_events(
        combined_events,
        event_type_filter,
        role_filter,
    )

    doc_count = len(visible_results)
    event_count = sum(event_type_counter.values())
    role_count = sum(role_counter.values())
    unique_trigger_words = len(trigger_word_counter)
    unique_argument_texts = len(argument_text_counter)

    sections: List[html.Div] = []

    if "overview" in selected_panels:
        sections.append(
            dbc.Row(
                [
                    dbc.Col(_build_kpi("Documents", doc_count, "Documents in the current view."), md=3, className="mb-3"),
                    dbc.Col(_build_kpi("Events", event_count, "Filtered events across selected modes."), md=3, className="mb-3"),
                    dbc.Col(_build_kpi("Roles", role_count, "Argument roles in the current selection."), md=3, className="mb-3"),
                    dbc.Col(_build_kpi("Trigger words", unique_trigger_words, "Distinct trigger words in the current selection."), md=3, className="mb-3"),
                ]
            )
        )

        sections.append(
            dbc.Row(
                [
                    dbc.Col(_build_kpi("Argument texts", unique_argument_texts, "Distinct extracted argument spans in the current selection."), md=12, className="mb-3"),
                ]
            )
        )

    if "schema_overview" in selected_panels:
        sections.append(
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Dataset / model coverage", className="mb-0")),
                    dbc.CardBody(_render_schema_overview(visible_results)),
                ],
                className="mb-4 shadow-sm",
            )
        )

    if "documents" in selected_panels:
        sections.append(
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Uploaded documents by ID", className="mb-0")),
                    dbc.CardBody(_render_documents_table(visible_results, selected_modes, event_type_filter, role_filter)),
                ],
                className="mb-4 shadow-sm",
            )
        )

    if "trigger_stats" in selected_panels:
        sections.append(
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=_figure_from_counter("Identified trigger words", trigger_counter, "#0d6efd")), md=12, className="mb-4"),
                ]
            )
        )

    if "argument_text_distribution" in selected_panels:
        sections.append(
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=_figure_from_counter("Argument text distribution", argument_text_counter, "#6f42c1")), md=12, className="mb-4"),
                ]
            )
        )

    if "event_type_distribution" in selected_panels:
        sections.append(
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=_figure_from_counter("Event type distribution", event_type_counter, "#198754")), md=12, className="mb-4"),
                ]
            )
        )

    if "argument_role_distribution" in selected_panels:
        sections.append(
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=_figure_from_counter("Argument role distribution", role_counter, "#fd7e14")), md=12, className="mb-4"),
                ]
            )
        )

    if "event_structures" in selected_panels:
        accordions = _event_cards(visible_results[0], selected_modes, event_type_filter, role_filter)
        if len(visible_results) > 1:
            for result in visible_results[1:]:
                accordions.extend(_event_cards(result, selected_modes, event_type_filter, role_filter))

        sections.append(
            dbc.Card(
                [
                    dbc.CardHeader(html.H5("Extracted event structures", className="mb-0")),
                    dbc.CardBody(
                        dbc.Accordion(accordions, start_collapsed=True)
                        if accordions
                        else html.P("No event structures match the current filters.", className="text-muted mb-0")
                    ),
                ],
                className="mb-4 shadow-sm",
            )
        )

    if not sections:
        return dbc.Alert("Select at least one panel to display.", color="warning")

    return html.Div(sections)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8052, dev_tools_hot_reload=False)