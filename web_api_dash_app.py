"""Dash + REST bridge for cross-domain event extraction.

This module keeps the existing Dash layout and callbacks from `web_dash_app.py`
unchanged, while adding HTTP GET/POST endpoints that expose the inference flow
from `infer.py`.

Use this entry point when you want the UI and the model calls to be reachable
through API routes instead of importing inference helpers directly in another
client.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from flask import jsonify, request

from infer import (
    parse_and_merge_single_inference_event_detection_results,
    present_parsed_output,
    run_single_inference_event_argument_extraction,
    run_single_inference_event_detection,
    run_single_inference_event_extraction_e2e,
    structure_argument_extraction_pipeline_predictions,
)
from web_dash_app import app, get_model_path, model_cache


server = app.server


def _read_request_payload() -> Dict[str, Any]:
    """Read input data from either query parameters or a JSON body."""
    if request.method == "GET":
        return dict(request.args)

    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload

    form_payload = request.form.to_dict()
    if form_payload:
        return form_payload

    return {}


def _parse_int(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_model(model_type: str, dataset: str):
    tokenizer_dir, model_dir = get_model_path(model_type, dataset)
    return model_cache.get_model(model_type, tokenizer_dir, model_dir)


def _base_params(payload: Dict[str, Any]) -> Tuple[str, str, str, str, int]:
    dataset = payload.get("dataset") or payload.get("domain") or payload.get("ds_key") or "geneva"
    model_type = payload.get("model_type") or "domain-specific"
    text = payload.get("text") or payload.get("source") or ""
    doc_id = payload.get("doc_id") or payload.get("id") or "api-doc"
    max_length = _parse_int(payload.get("max_length"), 512)
    return dataset, model_type, text, doc_id, max_length


def _ensure_text(text: str):
    if not text:
        return jsonify({"error": "Missing required field: text"}), 400
    return None


def _detection_payload(dataset: str, model_type: str, text: str, doc_id: str, max_length: int) -> Dict[str, Any]:
    model, tokenizer = _resolve_model(model_type, dataset)
    detection_item = run_single_inference_event_detection(
        doc_id=doc_id,
        tokenizer=tokenizer,
        model=model,
        ds_key=dataset,
        plain_text=text,
        max_length=max_length,
    )
    parsed_detection = parse_and_merge_single_inference_event_detection_results(detection_item)
    return {
        "dataset": dataset,
        "model_type": model_type,
        "doc_id": doc_id,
        "source": text,
        "event_detection_item": detection_item,
        "parsed_detection": parsed_detection,
    }


def _argument_payload(
    dataset: str,
    model_type: str,
    text: str,
    doc_id: str,
    max_length: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    parsed_detection = payload.get("parsed_detection")
    if not isinstance(parsed_detection, dict):
        detection_bundle = _detection_payload(dataset, model_type, text, doc_id, max_length)
        parsed_detection = detection_bundle["parsed_detection"]
    else:
        detection_bundle = {
            "dataset": dataset,
            "model_type": model_type,
            "doc_id": doc_id,
            "source": text,
            "parsed_detection": parsed_detection,
        }

    model, tokenizer = _resolve_model(model_type, dataset)
    ae_item = run_single_inference_event_argument_extraction(
        tokenizer=tokenizer,
        model=model,
        ds_key=dataset,
        plain_text=text,
        event_detection_item={
            "trigger_classification_pipeline": parsed_detection.get("trigger_classification_pipeline", []),
            "trigger_classification_e2e": parsed_detection.get("trigger_classification_e2e", []),
            "trigger_classification_merged": parsed_detection.get("trigger_classification_merged", []),
            "doc_id": parsed_detection.get("doc_id", doc_id),
            "source": text,
        },
        max_length=max_length,
    )

    parsed_argument_extractions = {
        "pipeline": structure_argument_extraction_pipeline_predictions(
            ae_item,
            parsed_detection.get("trigger_classification_pipeline", []),
            "argument_extraction_pipeline_pipeline",
        ),
        "e2e": structure_argument_extraction_pipeline_predictions(
            ae_item,
            parsed_detection.get("trigger_classification_e2e", []),
            "argument_extraction_pipeline_e2e",
        ),
        "merged": structure_argument_extraction_pipeline_predictions(
            ae_item,
            parsed_detection.get("trigger_classification_merged", []),
            "argument_extraction_pipeline_merged",
        ) if parsed_detection.get("trigger_classification_merged", []) else {},
    }

    return {
        **detection_bundle,
        "argument_extraction_item": ae_item,
        "parsed_argument_extractions": parsed_argument_extractions,
    }


def _e2e_payload(dataset: str, model_type: str, text: str, doc_id: str, max_length: int) -> Dict[str, Any]:
    model, tokenizer = _resolve_model(model_type, dataset)
    e2e_item = run_single_inference_event_extraction_e2e(
        doc_id=doc_id,
        tokenizer=tokenizer,
        model=model,
        ds_key=dataset,
        plain_text=text,
        max_length=max_length,
    )
    return {
        "dataset": dataset,
        "model_type": model_type,
        "doc_id": doc_id,
        "source": text,
        "event_extraction_item": e2e_item,
        "parsed_event_extraction": present_parsed_output(e2e_item),
    }


@server.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "ok",
        "app": "cross-domain-event-extraction",
        "endpoints": [
            "/api/health",
            "/api/pages",
            "/api/detect",
            "/api/arguments",
            "/api/e2e",
            "/api/infer",
        ],
    })


@server.route("/api/pages", methods=["GET"])
def api_pages():
    return jsonify({
        "pages": [
            {"path": "/", "name": "intro", "layout_factory": "create_intro_layout"},
            {"path": "/playground", "name": "playground", "layout_factory": "create_playground_layout"},
            {"path": "/app", "name": "extraction", "layout_factory": "create_extraction_layout"},
            {"path": "/dashboard", "name": "dashboard", "layout_factory": "create_insights_layout_page"},
        ]
    })


@server.route("/api/detect", methods=["GET", "POST"])
def api_detect():
    payload = _read_request_payload()
    dataset, model_type, text, doc_id, max_length = _base_params(payload)
    missing = _ensure_text(text)
    if missing is not None:
        return missing
    return jsonify(_detection_payload(dataset, model_type, text, doc_id, max_length))


@server.route("/api/arguments", methods=["GET", "POST"])
def api_arguments():
    payload = _read_request_payload()
    dataset, model_type, text, doc_id, max_length = _base_params(payload)
    missing = _ensure_text(text)
    if missing is not None:
        return missing
    return jsonify(_argument_payload(dataset, model_type, text, doc_id, max_length, payload))


@server.route("/api/e2e", methods=["GET", "POST"])
def api_e2e():
    payload = _read_request_payload()
    dataset, model_type, text, doc_id, max_length = _base_params(payload)
    missing = _ensure_text(text)
    if missing is not None:
        return missing
    return jsonify(_e2e_payload(dataset, model_type, text, doc_id, max_length))


@server.route("/api/infer", methods=["GET", "POST"])
def api_infer():
    payload = _read_request_payload()
    dataset, model_type, text, doc_id, max_length = _base_params(payload)
    missing = _ensure_text(text)
    if missing is not None:
        return missing

    detection_bundle = _detection_payload(dataset, model_type, text, doc_id, max_length)
    argument_bundle = _argument_payload(dataset, model_type, text, doc_id, max_length, {
        "parsed_detection": detection_bundle["parsed_detection"],
    })
    e2e_bundle = _e2e_payload(dataset, model_type, text, doc_id, max_length)

    return jsonify({
        "dataset": dataset,
        "model_type": model_type,
        "doc_id": doc_id,
        "source": text,
        "detection": detection_bundle,
        "arguments": argument_bundle,
        "e2e": e2e_bundle,
    })


if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=8051,
        dev_tools_hot_reload=False,
    )