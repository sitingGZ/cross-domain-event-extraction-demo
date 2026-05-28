"""
False-positive review app for argument extraction using Dash + Bootstrap.

Purpose:
- Review one false-positive sample at a time.
- Filter by dataset and model.
- Let annotators mark each FP as truly correct (missing annotation), truly false, or uncertain.
- Save decisions to JSONL for corrected precision analysis.

Input JSON format:
A list of records. The app is schema-flexible and tries multiple key aliases.
Recommended fields per record:
- fp_id (str)
- dataset (str)
- model_name (str)
- doc_id (str)
- source (str)
- trigger_text (str)
- trigger_type (str)
- argument_text (str)
- argument_role (str)
- prediction_item (dict, optional): raw infer.py output item
- parsed_prediction (dict, optional): parsed event structure

The app can parse prediction_item using infer.py helpers when present.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context

# Reuse parser helpers so display aligns with your inference pipeline.
from infer import (
    parse_and_merge_single_inference_event_detection_results,
    structure_argument_extraction_pipeline_predictions,
    present_parsed_output,
    parse_argument_extraction,
)

APP_TITLE = "Argument FP Re-check App"
DECISIONS = [
    {
        "label": "Truly Correct (likely missing gold annotation)",
        "value": "true_positive_missing_gold",
    },
    {
        "label": "Truly False Positive",
        "value": "true_false_positive",
    },
    {
        "label": "Uncertain / Needs discussion",
        "value": "uncertain",
    },
]

AE_TASK_OPTIONS = [
    {"label": "AE from Pipeline TC", "value": "argument_extraction_pipeline_pipeline"},
    {"label": "AE from E2E TC", "value": "argument_extraction_pipeline_e2e"},
]


def _first_non_empty(d: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def normalize_fp_record(raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Normalize many possible FP JSON formats into one schema."""
    fp_id = _first_non_empty(raw, ["fp_id", "id", "uid"], default=f"fp-{idx:07d}")
    dataset = _first_non_empty(raw, ["dataset", "ds_key", "domain"], default="unknown")
    model_name = _first_non_empty(raw, ["model_name", "model", "model_id"], default="unknown")
    doc_id = _first_non_empty(raw, ["doc_id", "document_id"], default="")
    source = _first_non_empty(raw, ["source", "text", "sentence", "document"], default="")

    trigger_text = _first_non_empty(raw, ["trigger_text", "pred_trigger_text", "trigger"], default="")
    trigger_type = _first_non_empty(raw, ["trigger_type", "pred_trigger_type", "event_type"], default="")
    argument_text = _first_non_empty(raw, ["argument_text", "pred_argument_text", "argument"], default="")
    argument_role = _first_non_empty(raw, ["argument_role", "pred_argument_role", "role"], default="")

    return {
        "fp_id": str(fp_id),
        "dataset": str(dataset),
        "model_name": str(model_name),
        "doc_id": str(doc_id),
        "source": str(source),
        "trigger_text": str(trigger_text),
        "trigger_type": str(trigger_type),
        "argument_text": str(argument_text),
        "argument_role": str(argument_role),
        "prediction_item": raw.get("prediction_item"),
        "parsed_prediction": raw.get("parsed_prediction"),
        "raw": raw,
    }


def normalize_fp_records(raw_data: Any) -> List[Dict[str, Any]]:
    if isinstance(raw_data, dict):
        # Allow wrapper format like {"records": [...]}.
        for key in ["records", "false_positives", "items", "data"]:
            if key in raw_data and isinstance(raw_data[key], list):
                raw_data = raw_data[key]
                break

    if not isinstance(raw_data, list):
        raise ValueError("Input JSON must be a list of records or a dict containing records list.")

    return [normalize_fp_record(x, i) for i, x in enumerate(raw_data)]


def parse_prediction_for_display(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Build a parsed event view using infer.py helpers when possible."""
    if rec.get("parsed_prediction"):
        return rec["parsed_prediction"]

    item = rec.get("prediction_item")
    if not isinstance(item, dict):
        return {"doc_id": rec.get("doc_id", ""), "source": rec.get("source", ""), "events": []}

    parsed = {
        "doc_id": item.get("doc_id", rec.get("doc_id", "")),
        "source": item.get("source", rec.get("source", "")),
        "events": [],
    }

    try:
        # Pipeline/e2e parsing from infer.py event-detection + argument outputs.
        det = parse_and_merge_single_inference_event_detection_results(item)
        trig = det.get("trigger_classification_merged") or det.get("trigger_classification_pipeline") or []

        # Pick whichever AE task prediction exists in this item.
        task_key = None
        for k in [
            "argument_extraction_pipeline_merged",
            "argument_extraction_pipeline_pipeline",
            "argument_extraction_pipeline_e2e",
        ]:
            if k in item:
                task_key = k
                break

        if task_key and trig:
            parsed = structure_argument_extraction_pipeline_predictions(item, trig, task_key)
        elif "event_extraction_e2e" in item:
            parsed = present_parsed_output(item)
    except Exception:
        pass

    return parsed


def build_event_cards(parsed: Dict[str, Any]) -> List[dbc.Card]:
    events = parsed.get("events", []) if isinstance(parsed, dict) else []
    cards: List[dbc.Card] = []
    for i, event in enumerate(events):
        trigger = event.get("trigger", {})
        args = event.get("arguments", [])

        trigger_line = html.Div(
            [
                html.Strong("Trigger: "),
                html.Span(trigger.get("text", "")),
                html.Span(f"  ({trigger.get('type', 'N/A')})", className="text-muted"),
            ]
        )

        arg_items: List[Any] = []
        for a in args:
            arg_items.append(
                html.Li(
                    [
                        html.Span(a.get("text", "")),
                        html.Span(f"  -> {a.get('role', 'N/A')}", className="text-muted"),
                    ]
                )
            )

        cards.append(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(f"Event {i + 1}", className="mb-2"),
                        trigger_line,
                        html.Hr(className="my-2"),
                        html.Div("Arguments:"),
                        html.Ul(arg_items if arg_items else [html.Li("None")], className="mb-0"),
                    ]
                ),
                className="mb-2",
            )
        )

    if not cards:
        cards = [dbc.Alert("No parsed events available for this sample.", color="light", className="mb-0")]
    return cards


def summary_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    datasets = sorted({r["dataset"] for r in records})
    models = sorted({r["model_name"] for r in records})
    return {"count": len(records), "datasets": datasets, "models": models}


def _extract_trigger_from_ae_pred(ae_str: str) -> Dict[str, str]:
    """Extract trigger text/type from an AE prediction string."""
    if not ae_str:
        return {"text": "", "type": ""}
    m = re.search(r"trigger>\s*(.*?)\s*>?=\s*([^:|]+)", ae_str)
    if not m:
        return {"text": "", "type": ""}
    return {"text": m.group(1).strip(), "type": m.group(2).strip()}


def build_argument_fp_records_from_pipeline_results(
    results: List[Dict[str, Any]],
    dataset: str,
    model_name: str,
    task_name: str,
) -> List[Dict[str, Any]]:
    """Build FP records directly from pipeline_and_e2e_predictions JSON content."""
    fp_records: List[Dict[str, Any]] = []

    for item in results:
        doc_id = str(item.get("doc_id", ""))
        source = str(item.get("source", ""))
        task_data = item.get(task_name, {}) if isinstance(item.get(task_name, {}), dict) else {}
        references = task_data.get("references", [])
        predictions = task_data.get("predictions", [])

        # Build reference (text, role) set exactly as metrics-style text-role matching.
        ref_text_role_set = set()
        for ref_str in references:
            for arg in parse_argument_extraction(source, ref_str):
                a_text = (arg.get("text") or "").strip()
                a_role = (arg.get("role") or "").strip()
                if a_text and a_role:
                    ref_text_role_set.add((a_text, a_role))

        local_idx = 0
        for pred_str in predictions:
            trig = _extract_trigger_from_ae_pred(pred_str)
            pred_args = parse_argument_extraction(source, pred_str)

            for arg in pred_args:
                a_text = (arg.get("text") or "").strip()
                a_role = (arg.get("role") or "").strip()
                a_offset = arg.get("offset") or []
                if not a_text or not a_role:
                    continue
                if (a_text, a_role) in ref_text_role_set:
                    continue

                parsed_preview = {
                    "doc_id": doc_id,
                    "source": source,
                    "events": [
                        {
                            "trigger": {
                                "text": trig.get("text", ""),
                                "type": trig.get("type", ""),
                                "offset": [],
                            },
                            "arguments": [
                                {
                                    "text": a_text,
                                    "role": a_role,
                                    "offset": a_offset,
                                }
                            ],
                        }
                    ],
                }

                fp_records.append(
                    {
                        "fp_id": f"{dataset}-{task_name}-{doc_id}-{local_idx}",
                        "dataset": dataset,
                        "model_name": model_name,
                        "task": task_name,
                        "doc_id": doc_id,
                        "source": source,
                        "trigger_text": trig.get("text", ""),
                        "trigger_type": trig.get("type", ""),
                        "argument_text": a_text,
                        "argument_role": a_role,
                        "argument_offset": a_offset,
                        "prediction_raw": pred_str,
                        "reference_candidates": references,
                        "parsed_prediction": parsed_preview,
                    }
                )
                local_idx += 1

    return fp_records


def load_fp_records_from_pipeline_file(
    pipeline_file: str,
    dataset: str,
    model_name: str,
    task_name: str,
) -> List[Dict[str, Any]]:
    """Load pipeline_and_e2e_predictions_*.json and derive FP records."""
    p = Path(pipeline_file).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Pipeline predictions file not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("Pipeline predictions file must contain a list of document items.")

    return build_argument_fp_records_from_pipeline_results(
        results=payload,
        dataset=dataset,
        model_name=model_name,
        task_name=task_name,
    )


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title=APP_TITLE)
server = app.server

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(html.H3(APP_TITLE), md=8),
                dbc.Col(
                    dbc.Input(id="reviewer-name", placeholder="Reviewer name", type="text"),
                    md=4,
                ),
            ],
            className="mt-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Upload(
                            id="upload-fp-json",
                            children=dbc.Button("Upload False-Positive JSON", color="primary"),
                            multiple=False,
                        ),
                        html.Div(id="upload-status", className="mt-2 text-muted"),
                    ],
                    md=4,
                ),
                dbc.Col(
                    dbc.Input(
                        id="pipeline-file-path",
                        placeholder="Path to pipeline_and_e2e_predictions_test.json",
                        type="text",
                    ),
                    md=4,
                ),
                dbc.Col(
                    dbc.Select(
                        id="pipeline-task-select",
                        options=AE_TASK_OPTIONS,
                        value="argument_extraction_pipeline_pipeline",
                    ),
                    md=2,
                ),
                dbc.Col(
                    dbc.Button("Load FP from Pipeline JSON", id="load-from-pipeline-btn", color="warning", className="w-100"),
                    md=2,
                ),
            ],
            className="g-2 mt-1",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Input(id="pipeline-dataset", placeholder="Dataset label (e.g., wikievents)", type="text", value="unknown"), md=4),
                dbc.Col(dbc.Input(id="pipeline-model-name", placeholder="Model name label", type="text", value="unknown-model"), md=4),
                dbc.Col(
                    dbc.Select(id="dataset-filter", options=[], value="__ALL__"),
                    md=3,
                ),
                dbc.Col(
                    dbc.Select(id="model-filter", options=[], value="__ALL__"),
                    md=3,
                ),
                dbc.Col(
                    dbc.Button("Save Annotations", id="save-annotations-btn", color="success", className="w-100"),
                    md=2,
                ),
            ],
            className="g-2 mt-1",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Alert(id="progress-alert", color="info", className="mt-3 mb-2"), md=12),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Current False Positive"),
                                html.Div(id="sample-meta", className="small text-muted mb-2"),
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.Div("Source Text", className="fw-bold mb-2"),
                                            html.Pre(id="source-text", style={"whiteSpace": "pre-wrap", "fontSize": "0.95rem"}),
                                        ]
                                    )
                                ),
                                html.Hr(),
                                dbc.Row(
                                    [
                                        dbc.Col(html.Div(id="candidate-summary"), md=12),
                                    ]
                                ),
                                html.Hr(),
                                html.Div("Parsed Prediction Context", className="fw-bold mb-2"),
                                html.Div(id="parsed-events-container"),
                            ]
                        )
                    ),
                    md=8,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Annotator Decision"),
                                dbc.RadioItems(
                                    id="decision-radio",
                                    options=DECISIONS,
                                    value=None,
                                    className="mb-3",
                                ),
                                dbc.Label("Notes"),
                                dbc.Textarea(id="decision-notes", placeholder="Why is this FP truly correct / false / uncertain?", rows=7),
                                dbc.Checkbox(id="schema-checked", label="Checked against schema/guidelines", value=False, className="mt-2"),
                                html.Hr(),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Button("Previous", id="prev-btn", color="secondary", className="w-100"), md=6),
                                        dbc.Col(dbc.Button("Save & Next", id="save-next-btn", color="primary", className="w-100"), md=6),
                                    ],
                                    className="g-2",
                                ),
                                html.Div(id="save-next-status", className="small text-muted mt-2"),
                            ]
                        )
                    ),
                    md=4,
                ),
            ],
            className="g-3",
        ),
        dcc.Store(id="fp-records-store", data=[]),
        dcc.Store(id="filtered-indices-store", data=[]),
        dcc.Store(id="cursor-store", data=0),
        dcc.Store(id="annotations-store", data={}),
    ],
    fluid=True,
)


@app.callback(
    Output("fp-records-store", "data"),
    Output("upload-status", "children"),
    Output("dataset-filter", "options"),
    Output("model-filter", "options"),
    Input("upload-fp-json", "contents"),
    State("upload-fp-json", "filename"),
)
def on_upload(contents: Optional[str], filename: Optional[str]):
    if not contents:
        raise dash.exceptions.PreventUpdate

    try:
        _, b64 = contents.split(",", 1)
        payload = json.loads(__import__("base64").b64decode(b64).decode("utf-8"))
        records = normalize_fp_records(payload)
        s = summary_stats(records)

        dataset_opts = [{"label": "All datasets", "value": "__ALL__"}] + [
            {"label": d, "value": d} for d in s["datasets"]
        ]
        model_opts = [{"label": "All models", "value": "__ALL__"}] + [
            {"label": m, "value": m} for m in s["models"]
        ]
        msg = f"Loaded {s['count']} records from {filename or 'uploaded file'}."
        return records, msg, dataset_opts, model_opts
    except Exception as e:
        return [], f"Failed to parse upload: {e}", [{"label": "All datasets", "value": "__ALL__"}], [{"label": "All models", "value": "__ALL__"}]


@app.callback(
    Output("fp-records-store", "data", allow_duplicate=True),
    Output("upload-status", "children", allow_duplicate=True),
    Output("dataset-filter", "options", allow_duplicate=True),
    Output("model-filter", "options", allow_duplicate=True),
    Input("load-from-pipeline-btn", "n_clicks"),
    State("pipeline-file-path", "value"),
    State("pipeline-dataset", "value"),
    State("pipeline-model-name", "value"),
    State("pipeline-task-select", "value"),
    prevent_initial_call=True,
)
def on_load_from_pipeline(
    n_clicks: Optional[int],
    pipeline_file_path: Optional[str],
    dataset: Optional[str],
    model_name: Optional[str],
    task_name: Optional[str],
):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    try:
        if not pipeline_file_path:
            raise ValueError("Please provide a pipeline predictions JSON file path.")

        records = load_fp_records_from_pipeline_file(
            pipeline_file=pipeline_file_path,
            dataset=(dataset or "unknown").strip() or "unknown",
            model_name=(model_name or "unknown-model").strip() or "unknown-model",
            task_name=task_name or "argument_extraction_pipeline_pipeline",
        )
        records = normalize_fp_records(records)
        s = summary_stats(records)

        dataset_opts = [{"label": "All datasets", "value": "__ALL__"}] + [
            {"label": d, "value": d} for d in s["datasets"]
        ]
        model_opts = [{"label": "All models", "value": "__ALL__"}] + [
            {"label": m, "value": m} for m in s["models"]
        ]

        msg = f"Loaded {s['count']} FP records derived directly from {pipeline_file_path}."
        return records, msg, dataset_opts, model_opts
    except Exception as e:
        return [], f"Failed to derive FP records from pipeline JSON: {e}", [{"label": "All datasets", "value": "__ALL__"}], [{"label": "All models", "value": "__ALL__"}]


@app.callback(
    Output("filtered-indices-store", "data"),
    Output("cursor-store", "data"),
    Input("fp-records-store", "data"),
    Input("dataset-filter", "value"),
    Input("model-filter", "value"),
)
def apply_filters(records: List[Dict[str, Any]], dataset: str, model_name: str):
    if not records:
        return [], 0

    indices: List[int] = []
    for i, r in enumerate(records):
        ok_dataset = dataset in (None, "__ALL__") or r.get("dataset") == dataset
        ok_model = model_name in (None, "__ALL__") or r.get("model_name") == model_name
        if ok_dataset and ok_model:
            indices.append(i)

    return indices, 0


@app.callback(
    Output("cursor-store", "data", allow_duplicate=True),
    Output("annotations-store", "data", allow_duplicate=True),
    Output("save-next-status", "children"),
    Input("save-next-btn", "n_clicks"),
    Input("prev-btn", "n_clicks"),
    State("cursor-store", "data"),
    State("filtered-indices-store", "data"),
    State("fp-records-store", "data"),
    State("annotations-store", "data"),
    State("decision-radio", "value"),
    State("decision-notes", "value"),
    State("schema-checked", "value"),
    State("reviewer-name", "value"),
    prevent_initial_call=True,
)
def navigate_and_save(
    save_next_clicks: Optional[int],
    prev_clicks: Optional[int],
    cursor: int,
    indices: List[int],
    records: List[Dict[str, Any]],
    annotations: Dict[str, Any],
    decision: Optional[str],
    notes: Optional[str],
    schema_checked: bool,
    reviewer_name: Optional[str],
):
    if not indices:
        return 0, annotations or {}, "No samples in current filter."

    annotations = annotations or {}
    trig = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""

    # Save current record decision only on Save & Next.
    if trig == "save-next-btn":
        idx = indices[cursor]
        rec = records[idx]
        ann_key = rec.get("fp_id", str(idx))
        annotations[ann_key] = {
            "fp_id": rec.get("fp_id"),
            "dataset": rec.get("dataset"),
            "model_name": rec.get("model_name"),
            "doc_id": rec.get("doc_id"),
            "decision": decision,
            "notes": notes or "",
            "schema_checked": bool(schema_checked),
            "reviewer": reviewer_name or "",
            "timestamp": datetime.utcnow().isoformat(),
        }
        next_cursor = min(cursor + 1, len(indices) - 1)
        return next_cursor, annotations, "Saved current decision."

    if trig == "prev-btn":
        prev_cursor = max(0, cursor - 1)
        return prev_cursor, annotations, "Moved to previous sample."

    return cursor, annotations, ""


@app.callback(
    Output("sample-meta", "children"),
    Output("source-text", "children"),
    Output("candidate-summary", "children"),
    Output("parsed-events-container", "children"),
    Output("progress-alert", "children"),
    Output("decision-radio", "value"),
    Output("decision-notes", "value"),
    Output("schema-checked", "value"),
    Input("cursor-store", "data"),
    Input("filtered-indices-store", "data"),
    Input("fp-records-store", "data"),
    Input("annotations-store", "data"),
)
def render_current(cursor: int, indices: List[int], records: List[Dict[str, Any]], annotations: Dict[str, Any]):
    if not indices or not records:
        return (
            "No sample loaded.",
            "",
            dbc.Alert("Upload a false-positive JSON file to begin.", color="warning"),
            html.Div(),
            "0 / 0 reviewed",
            None,
            "",
            False,
        )

    cursor = max(0, min(cursor, len(indices) - 1))
    rec = records[indices[cursor]]

    meta = f"Sample {cursor + 1}/{len(indices)} | FP ID: {rec.get('fp_id')} | Dataset: {rec.get('dataset')} | Model: {rec.get('model_name')} | Doc: {rec.get('doc_id')}"

    candidate = dbc.ListGroup(
        [
            dbc.ListGroupItem([html.Strong("Trigger: "), html.Span(f"{rec.get('trigger_text', '')} ({rec.get('trigger_type', '')})")]),
            dbc.ListGroupItem([html.Strong("Argument: "), html.Span(f"{rec.get('argument_text', '')} -> {rec.get('argument_role', '')}")]),
        ],
        flush=True,
    )

    parsed = parse_prediction_for_display(rec)
    cards = build_event_cards(parsed)

    ann_key = rec.get("fp_id", str(indices[cursor]))
    ann = (annotations or {}).get(ann_key, {})

    reviewed = sum(1 for i in indices if records[i].get("fp_id", str(i)) in (annotations or {}))
    progress = f"{reviewed} / {len(indices)} reviewed in current filter"

    return (
        meta,
        rec.get("source", ""),
        candidate,
        html.Div(cards),
        progress,
        ann.get("decision"),
        ann.get("notes", ""),
        ann.get("schema_checked", False),
    )


@app.callback(
    Output("upload-status", "children", allow_duplicate=True),
    Input("save-annotations-btn", "n_clicks"),
    State("annotations-store", "data"),
    State("reviewer-name", "value"),
    prevent_initial_call=True,
)
def save_annotations_to_disk(n_clicks: Optional[int], annotations: Dict[str, Any], reviewer_name: Optional[str]):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    annotations = annotations or {}
    out_dir = Path("annotation_results") / "fp_recheck"
    out_dir.mkdir(parents=True, exist_ok=True)

    reviewer = (reviewer_name or "reviewer").strip().replace(" ", "_")
    file_name = f"fp_recheck_{reviewer}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jsonl"
    out_path = out_dir / file_name

    with out_path.open("w", encoding="utf-8") as f:
        for _, item in annotations.items():
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return f"Saved {len(annotations)} annotations to {out_path}."


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8051)
