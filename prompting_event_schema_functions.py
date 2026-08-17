"""Prompt helpers for schema proposal and trigger/entity extraction.

This module provides two prompt-driven pipelines:
1. An open-source version that runs a local causal LM through Unsloth.
2. An OpenAI version that uses gpt-4o-mini via the OpenAI Python SDK.

Both versions perform two steps for a single input text:
- Stage 1: propose event labels and entity labels.
- Stage 2: identify trigger words and entity spans for the proposed labels.

The outputs are normalized to JSON-compatible Python dictionaries.
"""

import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pattern_tagprime import patterns, role_type_tags


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _sorted_schema_labels(dataset_key: str) -> Tuple[List[str], List[str]]:
    schema = patterns.get(dataset_key)
    if schema is None:
        available = ", ".join(sorted(patterns.keys()))
        raise KeyError(f"Unknown dataset key '{dataset_key}'. Available keys: {available}")

    event_labels = sorted(schema.keys())
    entity_labels = _dedupe_preserve_order(role for roles in schema.values() for role in roles)

    if not entity_labels:
        role_map = role_type_tags.get(dataset_key, {})
        entity_labels = sorted(role_map.keys())

    return event_labels, entity_labels


def _format_label_block(title: str, labels: Sequence[str]) -> str:
    if not labels:
        return f"{title}: []"
    return f"{title}: [{', '.join(labels)}]"


def _json_prompt_instruction() -> str:
    return (
        "Return only valid JSON. Do not wrap the answer in markdown or code fences. "
        "Use the exact keys: {\"event labels\": [...], \"entity labels\": [...]} for stage 1, "
        "and {\"triggers\": [[word, event label], ...], \"entities\": [[word, entity label], ...]} for stage 2. "
        "If nothing is found, return empty arrays."
    )


def build_stage1_messages(
    text: str,
    dataset_key: str = "geneva",
    max_event_labels: Optional[int] = None,
    max_entity_labels: Optional[int] = None,
) -> List[Dict[str, str]]:
    """Build messages for the label-proposal step."""
    event_labels, entity_labels = _sorted_schema_labels(dataset_key)
    if max_event_labels is not None:
        event_labels = event_labels[:max_event_labels]
    if max_entity_labels is not None:
        entity_labels = entity_labels[:max_entity_labels]

    schema_block = "\n".join(
        [
            f"Dataset: {dataset_key}",
            _format_label_block("Allowed event labels", event_labels),
            _format_label_block("Allowed entity labels", entity_labels),
            "Task: infer the smallest useful subset of event labels and entity labels that are supported by the text.",
            _json_prompt_instruction(),
        ]
    )

    return [
        {
            "role": "system",
            "content": (
                "You are an information extraction assistant that only emits JSON and never explains its reasoning. "
                "Use the provided schema inventory to choose labels supported by the text."
            ),
        },
        {
            "role": "user",
            "content": f"{schema_block}\n\nText:\n{text}",
        },
    ]


def build_stage2_messages(
    text: str,
    event_labels: Sequence[str],
    entity_labels: Sequence[str],
) -> List[Dict[str, str]]:
    """Build messages for the trigger/entity extraction step."""
    event_labels = _dedupe_preserve_order(event_labels)
    entity_labels = _dedupe_preserve_order(entity_labels)

    schema_block = "\n".join(
        [
            "You are now identifying exact text spans.",
            _format_label_block("Proposed event labels", event_labels),
            _format_label_block("Proposed entity labels", entity_labels),
            "Task: identify trigger words for the proposed event labels and entity spans for the proposed entity labels.",
            "Use exact words or short phrases copied from the text.",
            _json_prompt_instruction(),
        ]
    )

    return [
        {
            "role": "system",
            "content": (
                "You are a precise event extraction assistant. Output only JSON with arrays of pairs. "
                "A JSON pair should be represented as a two-item array, not as an object."
            ),
        },
        {
            "role": "user",
            "content": f"{schema_block}\n\nText:\n{text}",
        },
    ]


def build_chat_prompt(tokenizer: Any, messages: Sequence[Dict[str, str]]) -> str:
    """Render messages into a prompt string for chat-tuned models."""
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(list(messages), tokenize=False, add_generation_prompt=True)
        except Exception:
            pass

    chunks: List[str] = []
    for message in messages:
        role = str(message.get("role", "user")).upper()
        content = str(message.get("content", ""))
        chunks.append(f"[{role}]\n{content}")
    chunks.append("[ASSISTANT]\n")
    return "\n\n".join(chunks)


def _extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if "```" in cleaned:
        cleaned = cleaned.replace("```json", "```")
        parts = cleaned.split("```")
        if len(parts) >= 3:
            cleaned = parts[1].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not find a JSON object in: {text}")

    return json.loads(cleaned[start : end + 1])


def _normalize_stage1_result(result: Dict[str, Any]) -> Dict[str, List[str]]:
    event_labels = result.get("event labels", [])
    entity_labels = result.get("entity labels", [])

    if not isinstance(event_labels, list):
        event_labels = []
    if not isinstance(entity_labels, list):
        entity_labels = []

    return {
        "event labels": _dedupe_preserve_order(event_labels),
        "entity labels": _dedupe_preserve_order(entity_labels),
    }


def _normalize_pair_list(value: Any) -> List[List[str]]:
    if not isinstance(value, list):
        return []

    normalized: List[List[str]] = []
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            word = str(item[0]).strip()
            label = str(item[1]).strip()
            if word and label:
                normalized.append([word, label])
    return normalized


def _normalize_stage2_result(result: Dict[str, Any]) -> Dict[str, List[List[str]]]:
    return {
        "triggers": _normalize_pair_list(result.get("triggers", [])),
        "entities": _normalize_pair_list(result.get("entities", [])),
    }


def build_pos_messages(text: str) -> List[Dict[str, str]]:
    """Build messages to request part-of-speech tagging for the input text.

    Output JSON should use the key `pos` with a list of two-item arrays: [[word, tag], ...]
    """
    schema_block = "\n".join(
        [
            "Task: produce part-of-speech tags for each significant token in the text.",
            "Return JSON with key 'pos' and a list of [word, POS] pairs.",
            _json_prompt_instruction(),
        ]
    )

    return [
        {"role": "system", "content": "You are a POS tagger assistant. Output only JSON."},
        {"role": "user", "content": f"{schema_block}\n\nText:\n{text}"},
    ]


def build_dep_messages(text: str) -> List[Dict[str, str]]:
    """Build messages to request dependency parse relations for the input text.

    Output JSON should use the key `dependencies` with a list of three-item arrays:
    [[governor, dependent, relation], ...]
    """
    schema_block = "\n".join(
        [
            "Task: produce dependency relations for the sentence(s) in the text.",
            "Return JSON with key 'dependencies' and a list of [governor, dependent, relation] triples.",
            _json_prompt_instruction(),
        ]
    )

    return [
        {"role": "system", "content": "You are a dependency parser assistant. Output only JSON."},
        {"role": "user", "content": f"{schema_block}\n\nText:\n{text}"},
    ]


def _normalize_pos(result: Dict[str, Any]) -> List[List[str]]:
    raw = result.get("pos", [])
    return _normalize_pair_list(raw)


def _normalize_dependencies(result: Dict[str, Any]) -> List[List[str]]:
    raw = result.get("dependencies", [])
    if not isinstance(raw, list):
        return []
    normalized: List[List[str]] = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            gov = str(item[0]).strip()
            dep = str(item[1]).strip()
            rel = str(item[2]).strip()
            if gov and dep and rel:
                normalized.append([gov, dep, rel])
    return normalized


def _generate_with_unsloth(model: Any, tokenizer: Any, messages: Sequence[Dict[str, str]], max_new_tokens: int = 256, temperature: float = 0.0) -> str:
    import torch

    prompt = build_chat_prompt(tokenizer, messages)
    encoded = tokenizer(prompt, return_tensors="pt")
    device = next(model.parameters()).device
    encoded = {key: value.to(device) for key, value in encoded.items()}

    generation_kwargs: Dict[str, Any] = {"max_new_tokens": max_new_tokens, "pad_token_id": tokenizer.eos_token_id}
    if temperature and temperature > 0.0:
        generation_kwargs.update({"do_sample": True, "temperature": temperature})

    with torch.no_grad():
        output_ids = model.generate(**encoded, **generation_kwargs)

    prompt_length = encoded["input_ids"].shape[1]
    generated_text = tokenizer.decode(output_ids[0][prompt_length:], skip_special_tokens=True)
    return generated_text.strip()


def run_two_stage_prompting_unsloth(
    text: str,
    dataset_key: str = "geneva",
    model_name: str = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
    max_seq_length: int = 4096,
    load_in_4bit: bool = True,
    temperature: float = 0.0,
    max_new_tokens: int = 256,
    max_event_labels: Optional[int] = None,
    max_entity_labels: Optional[int] = None,
    include_pos: bool = False,
    include_dep: bool = False,
) -> Dict[str, Any]:
    """Run the two-stage prompting pipeline with a local Unsloth model."""
    try:
        from unsloth import FastLanguageModel
    except ImportError as exc:  # pragma: no cover - runtime dependency check
        raise ImportError("unsloth is required for run_two_stage_prompting_unsloth") from exc

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=load_in_4bit,
    )
    if hasattr(FastLanguageModel, "for_inference"):
        model = FastLanguageModel.for_inference(model)
    model.eval()

    stage1_messages = build_stage1_messages(
        text=text,
        dataset_key=dataset_key,
        max_event_labels=max_event_labels,
        max_entity_labels=max_entity_labels,
    )
    stage1_text = _generate_with_unsloth(model, tokenizer, stage1_messages, max_new_tokens=max_new_tokens, temperature=temperature)
    stage1 = _normalize_stage1_result(_extract_json_object(stage1_text))

    stage2_messages = build_stage2_messages(
        text=text,
        event_labels=stage1["event labels"],
        entity_labels=stage1["entity labels"],
    )
    stage2_text = _generate_with_unsloth(model, tokenizer, stage2_messages, max_new_tokens=max_new_tokens, temperature=temperature)
    stage2 = _normalize_stage2_result(_extract_json_object(stage2_text))

    pos = []
    dependencies = []
    if include_pos:
        pos_text = _generate_with_unsloth(model, tokenizer, build_pos_messages(text), max_new_tokens=max_new_tokens, temperature=temperature)
        try:
            pos = _normalize_pos(_extract_json_object(pos_text))
        except Exception:
            pos = []
    if include_dep:
        dep_text = _generate_with_unsloth(model, tokenizer, build_dep_messages(text), max_new_tokens=max_new_tokens, temperature=temperature)
        try:
            dependencies = _normalize_dependencies(_extract_json_object(dep_text))
        except Exception:
            dependencies = []

    return {
        "stage 1": stage1,
        "stage 2": stage2,
        "stage 1 raw": stage1_text,
        "stage 2 raw": stage2_text,
        "pos": pos,
        "dependencies": dependencies,
    }


def run_two_stage_prompting_openai(
    text: str,
    dataset_key: str = "geneva",
    client: Any = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
    max_event_labels: Optional[int] = None,
    max_entity_labels: Optional[int] = None,
    include_pos: bool = False,
    include_dep: bool = False,
) -> Dict[str, Any]:
    """Run the two-stage prompting pipeline with OpenAI's chat completions API."""
    if client is None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - runtime dependency check
            raise ImportError("openai is required for run_two_stage_prompting_openai") from exc

        client = OpenAI()

    stage1_messages = build_stage1_messages(
        text=text,
        dataset_key=dataset_key,
        max_event_labels=max_event_labels,
        max_entity_labels=max_entity_labels,
    )
    stage1_response = client.chat.completions.create(
        model=model,
        messages=stage1_messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    stage1_text = stage1_response.choices[0].message.content or "{}"
    stage1 = _normalize_stage1_result(_extract_json_object(stage1_text))

    stage2_messages = build_stage2_messages(
        text=text,
        event_labels=stage1["event labels"],
        entity_labels=stage1["entity labels"],
    )
    stage2_response = client.chat.completions.create(
        model=model,
        messages=stage2_messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    stage2_text = stage2_response.choices[0].message.content or "{}"
    stage2 = _normalize_stage2_result(_extract_json_object(stage2_text))

    pos = []
    dependencies = []
    if include_pos:
        pos_msgs = build_pos_messages(text)
        pos_resp = client.chat.completions.create(model=model, messages=pos_msgs, temperature=temperature, response_format={"type": "json_object"})
        pos_text = pos_resp.choices[0].message.content or "{}"
        try:
            pos = _normalize_pos(_extract_json_object(pos_text))
        except Exception:
            pos = []
    if include_dep:
        dep_msgs = build_dep_messages(text)
        dep_resp = client.chat.completions.create(model=model, messages=dep_msgs, temperature=temperature, response_format={"type": "json_object"})
        dep_text = dep_resp.choices[0].message.content or "{}"
        try:
            dependencies = _normalize_dependencies(_extract_json_object(dep_text))
        except Exception:
            dependencies = []

    return {
        "stage 1": stage1,
        "stage 2": stage2,
        "stage 1 raw": stage1_text,
        "stage 2 raw": stage2_text,
        "pos": pos,
        "dependencies": dependencies,
    }


def propose_and_extract_with_unsloth(
    model: Any,
    tokenizer: Any,
    text: str,
    dataset_key: str = "geneva",
    temperature: float = 0.0,
    max_new_tokens: int = 256,
    include_pos: bool = False,
    include_dep: bool = False,
) -> Dict[str, Any]:
    """Use an already-loaded Unsloth model for the same two-stage workflow."""
    stage1_messages = build_stage1_messages(text=text, dataset_key=dataset_key)
    stage1_text = _generate_with_unsloth(model, tokenizer, stage1_messages, max_new_tokens=max_new_tokens, temperature=temperature)
    stage1 = _normalize_stage1_result(_extract_json_object(stage1_text))

    stage2_messages = build_stage2_messages(text=text, event_labels=stage1["event labels"], entity_labels=stage1["entity labels"])
    stage2_text = _generate_with_unsloth(model, tokenizer, stage2_messages, max_new_tokens=max_new_tokens, temperature=temperature)
    stage2 = _normalize_stage2_result(_extract_json_object(stage2_text))

    pos = []
    dependencies = []
    if include_pos:
        pos_text = _generate_with_unsloth(model, tokenizer, build_pos_messages(text), max_new_tokens=max_new_tokens, temperature=temperature)
        try:
            pos = _normalize_pos(_extract_json_object(pos_text))
        except Exception:
            pos = []
    if include_dep:
        dep_text = _generate_with_unsloth(model, tokenizer, build_dep_messages(text), max_new_tokens=max_new_tokens, temperature=temperature)
        try:
            dependencies = _normalize_dependencies(_extract_json_object(dep_text))
        except Exception:
            dependencies = []

    return {"stage 1": stage1, "stage 2": stage2, "pos": pos, "dependencies": dependencies}


def propose_and_extract_with_openai(
    client: Any,
    text: str,
    dataset_key: str = "geneva",
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
    include_pos: bool = False,
    include_dep: bool = False,
) -> Dict[str, Any]:
    """Use an already-created OpenAI client for the same two-stage workflow."""
    stage1_messages = build_stage1_messages(text=text, dataset_key=dataset_key)
    stage1_response = client.chat.completions.create(
        model=model,
        messages=stage1_messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    stage1 = _normalize_stage1_result(_extract_json_object(stage1_response.choices[0].message.content or "{}"))

    stage2_messages = build_stage2_messages(text=text, event_labels=stage1["event labels"], entity_labels=stage1["entity labels"])
    stage2_response = client.chat.completions.create(
        model=model,
        messages=stage2_messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    stage2 = _normalize_stage2_result(_extract_json_object(stage2_response.choices[0].message.content or "{}"))

    pos = []
    dependencies = []
    if include_pos:
        pos_resp = client.chat.completions.create(model=model, messages=build_pos_messages(text), temperature=temperature, response_format={"type": "json_object"})
        try:
            pos = _normalize_pos(_extract_json_object(pos_resp.choices[0].message.content or "{}"))
        except Exception:
            pos = []
    if include_dep:
        dep_resp = client.chat.completions.create(model=model, messages=build_dep_messages(text), temperature=temperature, response_format={"type": "json_object"})
        try:
            dependencies = _normalize_dependencies(_extract_json_object(dep_resp.choices[0].message.content or "{}"))
        except Exception:
            dependencies = []

    return {"stage 1": stage1, "stage 2": stage2, "pos": pos, "dependencies": dependencies}


__all__ = [
    "build_stage1_messages",
    "build_stage2_messages",
    "build_chat_prompt",
    "propose_and_extract_with_unsloth",
    "propose_and_extract_with_openai",
    "run_two_stage_prompting_unsloth",
    "run_two_stage_prompting_openai",
]