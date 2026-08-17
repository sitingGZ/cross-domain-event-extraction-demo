"""
Single-sample web inference helper for T5 event extraction pipeline.

Provides two stages:
- Stage 1: Trigger Identification + Trigger Classification (pipeline and e2e)
- Stage 2: Argument Extraction (based on TC pipeline OR TC e2e)

Optional: Event Extraction E2E, or merge all results.

Outputs either JSON (default) or HTML for web display.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import uuid
from typing import Dict, List
import re

from transformers import T5ForConditionalGeneration, AutoTokenizer

# Reuse existing pipeline helpers and parsers
from t5_event_predict import predict, batch_predict
from parse_task_outputs import (
	_clean,
	parse_triggers_from_tagged,
	parse_tc_pairs
)

from t5_event_predict_pipeline import (
    build_trigger_classification_input_pipeline,
    build_trigger_classification_input_e2e
)

from pattern_tagprime import patterns, role_type_tags

DATASETS = ["geneva", "wikievents", "casie", "genia2013", "m2e2", "rams"]


def add_space_around_punctuation(text: str) -> str:
    """
    Add spaces between punctuation and characters to match model input preprocessing.
    
    Example:
        'U.S. authorities' -> 'U . S . authorities'
        'don't' -> 'don ' t'
    
    Args:
        text: Original text string
    
    Returns:
        Text with spaces added around punctuation
    """
    # Add space before and after each punctuation character
    result = re.sub(r'([^\w\s])', r' \1 ', text)
    # Normalize multiple spaces to single space
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def build_trigger_identification_input(ds_key: str, plain_text: str) -> str:
    # Identification prompt consistent with other Domain-prefixed tasks
    #identification_task_prompt = "Identify trigger words.", classification_e2e_task_prompt = "Classify trigger types end-to-end."
    #classification_task_prompt = "Classify trigger types."
    return f"Domain: {ds_key}. Identify trigger words. {plain_text}"

def build_event_extraction_e2e_input(ds_key: str, plain_text: str) -> str:
    # Matches existing annotation format used in repo
    #e2e_task_prompt = "Event trigger and argument extraction."
    return f"domain: {ds_key}. Event trigger and argument extraction. {plain_text}"



def find_word_position(text, word, start_from=0):
    """Find position of word as a whole word, not substring."""
    # Use word boundary regex to match complete words only
    pattern = r'\b' + re.escape(word) + r'\b'
    match = re.search(pattern, text[start_from:])
    if match:
        # Adjust position to account for start_from offset
        return start_from + match.start()
    return -1

def find_all_word_positions(text, word):
    """Find all positions of word as a whole word, not substring.
    
    Args:
        text: Text to search in
        word: Word to find
    
    Returns:
        List of starting positions where the word appears
    """
    positions = []
    pattern = r'\b' + re.escape(word) + r'\b'
    for match in re.finditer(pattern, text):
        positions.append(match.start())
    return positions

def find_all_substring_positions(text, substring):
    """Find all positions of substring.
    
    Args:
        text: Text to search in
        substring: Substring to find
    
    Returns:
        List of starting positions where the substring appears
    """
    positions = []
    start = 0
    while True:
        pos = text.find(substring, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    return positions

def find_text_with_word_fallback(text, search_term, trigger_offset=None):
    """Find text with progressive word removal fallback.
    
    If search_term is not found as a complete match, progressively remove words from the end
    until a match is found. Returns all positions for the best (most complete) match found,
    along with the actual matched text.
    
    Args:
        text: Source text to search in
        search_term: Text to find (may contain multiple words)
        trigger_offset: Optional [trigger_start, trigger_end] offset for proximity ranking
    
    Returns:
        Tuple of (positions, matched_text) where:
        - positions: List of positions where the best match was found, or empty list if no match
        - matched_text: The actual text that was found (may be shorter than search_term)
    
    Example:
        If search_term='big city around' and text doesn't contain it:
        - Tries 'big city around' (not found)
        - Tries 'big city' (found at positions [0, 45, 100])
        - Returns ([0, 45, 100], 'big city')
    """
    words = search_term.split()
    
    # Try progressively shorter versions by removing words from the end
    for i in range(len(words), 0, -1):
        current_term = ' '.join(words[:i])
        positions = find_all_substring_positions(text, current_term)
        
        if positions:
            # Found a match at this level, return positions and matched text
            return positions, current_term
    
    # No match found at any level
    return [], search_term

def select_closest_offset(text, keyword, trigger_offset=None, is_word_boundary=False):
    """Select the offset of keyword occurrence closest to trigger offset.
    
    If trigger_offset is None, returns the first occurrence.
    If trigger_offset is provided:
    - If all occurrences are before trigger: take the largest offset (closest to trigger start)
    - If all occurrences are after trigger: take the smallest offset (closest to trigger end)
    - If occurrences span both sides: take the closest one
    
    Args:
        text: Source text
        keyword: Word or substring to find
        trigger_offset: [trigger_start, trigger_end] offset, or None
        is_word_boundary: Whether to use word boundary search
    
    Returns:
        Starting position of selected occurrence, or -1 if not found
    """
    if is_word_boundary:
        positions = find_all_word_positions(text, keyword)
    else:
        positions = find_all_substring_positions(text, keyword)
    
    if not positions:
        return -1
    
    # If no trigger offset provided or only one position, return first
    if trigger_offset is None or len(positions) == 1:
        return positions[0]
    
    trigger_start = trigger_offset[0]
    trigger_end = trigger_offset[1]
    
    # Separate positions into before and after trigger
    before_positions = [p for p in positions if p < trigger_start]
    after_positions = [p for p in positions if p > trigger_end]
    
    # If all positions are before trigger, take the largest (closest to trigger)
    if before_positions and not after_positions:
        return max(before_positions)
    
    # If all positions are after trigger, take the smallest (closest to trigger)
    if after_positions and not before_positions:
        return min(after_positions)
    
    # If positions exist on both sides, find closest one
    if before_positions and after_positions:
        closest_before = max(before_positions)
        closest_after = min(after_positions)
        # Distance from closest_before to trigger_start
        dist_before = trigger_start - closest_before
        # Distance from trigger_end to closest_after
        dist_after = closest_after - trigger_end
        return closest_before if dist_before <= dist_after else closest_after
    
    # Fallback to first position
    return positions[0]

def select_closest_from_positions(positions, trigger_offset=None):
    """Select the closest position to trigger offset from a list of positions.
    
    Args:
        positions: List of positions to choose from
        trigger_offset: [trigger_start, trigger_end] offset, or None
    
    Returns:
        Selected position, or first position if only one or no trigger offset
    """
    if not positions:
        return -1
    
    if trigger_offset is None or len(positions) == 1:
        return positions[0]
    
    trigger_start = trigger_offset[0]
    trigger_end = trigger_offset[1]
    
    # Separate positions into before and after trigger
    before_positions = [p for p in positions if p < trigger_start]
    after_positions = [p for p in positions if p > trigger_end]
    
    # If all positions are before trigger, take the largest (closest to trigger)
    if before_positions and not after_positions:
        return max(before_positions)
    
    # If all positions are after trigger, take the smallest (closest to trigger)
    if after_positions and not before_positions:
        return min(after_positions)
    
    # If positions exist on both sides, find closest one
    if before_positions and after_positions:
        closest_before = max(before_positions)
        closest_after = min(after_positions)
        # Distance from closest_before to trigger_start
        dist_before = trigger_start - closest_before
        # Distance from trigger_end to closest_after
        dist_after = closest_after - trigger_end
        return closest_before if dist_before <= dist_after else closest_after
    
    # Fallback to first position
    return positions[0]

def construct_t5_model(
    tokenizer_dir: str,
    model_dir: str):
    model = T5ForConditionalGeneration.from_pretrained(model_dir)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
    device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    return model, tokenizer
    

def run_single_inference_event_detection(
    doc_id,
    tokenizer,
    model,
    ds_key: str,
    plain_text: str,
    max_length: int = 512,
    ) -> Dict:
    item: Dict = {
        #"doc_id": f"user-{uuid.uuid4().hex[:8]}",
        "doc_id": doc_id,
        "source": plain_text,
        "trigger_identification": {},
        "trigger_classification_pipeline": {},
        "trigger_classification_e2e": {}
    }
    # Trigger Identification
    ti_input = build_trigger_identification_input(ds_key, plain_text)
    item["trigger_identification"].update({"input": ti_input, "reference": ""})
    ti_pred = predict(model, tokenizer, ti_input, max_length=max_length)
    if isinstance(ti_pred, list):
        ti_pred = ti_pred[0] if ti_pred else ""
    item["trigger_identification"].update({"prediction": ti_pred})

    # Trigger Classification (pipeline)
    tc_input = build_trigger_classification_input_pipeline(ds_key, ti_pred) if ti_pred else ""
    item["trigger_classification_pipeline"].update({"input": tc_input, "reference": ""})
    tc_pred = predict(model, tokenizer, tc_input, max_length=max_length) if tc_input else ""
    if isinstance(tc_pred, list):
        tc_pred = tc_pred[0] if tc_pred else ""
    item["trigger_classification_pipeline"].update({"prediction": tc_pred})

    # Trigger Classification (e2e)
    tc_input_e2e = build_trigger_classification_input_e2e(ds_key, plain_text)
    item["trigger_classification_e2e"].update({"input": tc_input_e2e, "reference": ""})
    tc_pred_e2e = predict(model, tokenizer, tc_input_e2e, max_length=max_length)
    if isinstance(tc_pred_e2e, list):
        tc_pred_e2e = tc_pred_e2e[0] if tc_pred_e2e else ""
    item["trigger_classification_e2e"].update({"prediction": tc_pred_e2e})
    return item


def parse_and_merge_single_inference_event_detection_results(event_detection_item: Dict) -> Dict:
    """Parse the TI + TC results of TC pipeline and TC e2e into structured event format. 
       In addition, if TC pipeline and TC e2e are different, merges both pipeline and e2e TC results, otherwise no need to merge.
       Returns:
       item: Dict with parsed TC pipeline, TC e2e, and merged trigger classification results.
    """
    source = event_detection_item.get("source", "")
    item = {
        "doc_id": event_detection_item.get("doc_id", ""),
        "source": source,
        "trigger_classification_pipeline": [],
        "trigger_classification_e2e": [],
        "trigger_classification_merged": [],
    }
    # Parse triggers from both TC pipeline and TC e2e
    tc_pipeline_pred = event_detection_item.get("trigger_classification_pipeline", {}).get("prediction", "")
    tc_e2e_pred = event_detection_item.get("trigger_classification_e2e", {}).get("prediction", "")
   
    triggers_pipeline = parse_trigger_identification_classification(source, tc_pipeline_pred) if tc_pipeline_pred else []
    triggers_e2e = parse_trigger_identification_classification(source, tc_e2e_pred) if tc_e2e_pred else []

    # Normalize keys: parser returns {text,type,offset}
    item["trigger_classification_pipeline"] = [
        (t.get('text', ''), t.get('type', ''), t.get('offset', [])) for t in triggers_pipeline
    ]
    item["trigger_classification_e2e"] = [
        (t.get('text', ''), t.get('type', ''), t.get('offset', [])) for t in triggers_e2e
    ]
    
    # Merge triggers from both sources, avoiding duplicates by (text, type, offset)
    merged_map = {}
    for t in triggers_pipeline + triggers_e2e:
        key = (t.get('text', ''), t.get('type', ''), tuple(t.get('offset', [])))
        # keep earliest occurrence
        if key not in merged_map:
            merged_map[key] = t

    merged_triggers = list(merged_map.values())

    # If merged adds no new triggers beyond one set, skip merged output
    if len(merged_triggers) == len(triggers_pipeline) or len(merged_triggers) == len(triggers_e2e):
        item["trigger_classification_merged"] = []
    else:
        merged_triggers.sort(key=lambda x: x.get("offset", [0, 0])[0] if x.get("offset") else 0)
        item["trigger_classification_merged"] = [
            (t.get('text', ''), t.get('type', ''), t.get('offset', [])) for t in merged_triggers
        ]
    return item

def build_argument_extraction_input(
    ds_key: str,
    original_text: str,
    trigger_text: str,
    event_type: str
) -> str:
    """
    Build argument extraction input for a specific trigger from TC prediction.
    """
    # Get roles for this event type using role_type_tags first, then patterns fallback
    #roles = role_type_tags.get(ds_key, {}).get(event_type, [])
    #if not roles:
    #    try:
    #        ds_patterns = patterns.get(ds_key, {})
    #        if event_type and event_type in ds_patterns:
    #            roles = ds_patterns.get(event_type, [])
    #        else:
    #            for k in ds_patterns.keys():
    #                if k.lower() == (event_type or "").lower():
    #                    roles = ds_patterns.get(k, [])
    #                    break
    #    except Exception:
    #        roles = []
    roles = []
    try:
      ds_patterns = patterns.get(ds_key, {})
      if event_type and event_type in ds_patterns:
        roles = ds_patterns.get(event_type, [])
      else:
        for k in ds_patterns.keys():
          if k.lower() == (event_type or "").lower():
            roles = ds_patterns.get(k, [])
            break
    except Exception:
      roles = []
    roles_str = " | ".join(roles) if roles else ""

    # Debug logging if roles are empty
    if not roles_str:
        print(f"WARNING: No roles found for ds_key={ds_key}, event_type={event_type}")
        #print(f"  Available keys in role_type_tags[{ds_key}]: {list(role_type_tags.get(ds_key, {}).keys())[:5]}...")
    
    # If roles_str is empty, still generate the input but note the missing roles
    return (
        f"Domain: {ds_key}. Extract arguments for a specific event. "
        f"argument> {roles_str} for trigger> {trigger_text}>={event_type}: {original_text}"
    )


def run_single_inference_event_argument_extraction(
    tokenizer,
    model,
    ds_key: str,
    plain_text: str,
    event_detection_item: Dict,
    max_length: int = 512,
) -> Dict:
    # Load model/tokenizer
    doc_id = event_detection_item.get("doc_id", "")
    item: Dict = {
        "doc_id": doc_id,
        "source": plain_text,
        "argument_extraction_pipeline_pipeline": {},
        "argument_extraction_pipeline_e2e": {},
        "argument_extraction_pipeline_merged": {},
    }

    
    # Argument Extraction based on TC pipeline
    ae_inputs: List[str] = []
    ae_predictions: List[str] = []
    ae_refs: List[str] = []
    tc_pairs_pipeline = event_detection_item.get("trigger_classification_pipeline", [])
    if tc_pairs_pipeline and isinstance(tc_pairs_pipeline, list):
        for trigger_idx, (_trigger_text, _event_type, _) in enumerate(tc_pairs_pipeline):
            ae_input = build_argument_extraction_input(ds_key, plain_text, _trigger_text, _event_type)
            if ae_input:
                ae_inputs.append(ae_input)
    if ae_inputs:
        ae_predictions = batch_predict(model, tokenizer, ae_inputs, max_length=max_length)
    item["argument_extraction_pipeline_pipeline"].update({
        "inputs": ae_inputs,
        "references": ae_refs,
        "predictions": ae_predictions,
    })

    # Argument Extraction based on TC e2e
    ae_inputs_e2e: List[str] = []
    ae_predictions_e2e: List[str] = []
    ae_refs_e2e: List[str] = []
    tc_pairs_e2e = event_detection_item.get("trigger_classification_e2e", [])
    if tc_pairs_e2e and isinstance(tc_pairs_e2e, list):
        for trigger_idx, (_trigger_text, _event_type, _) in enumerate(tc_pairs_e2e):
            ae_input_e2e = build_argument_extraction_input(ds_key, plain_text, _trigger_text, _event_type)
            if ae_input_e2e:
                ae_inputs_e2e.append(ae_input_e2e)
    if ae_inputs_e2e:
        ae_predictions_e2e = batch_predict(model, tokenizer, ae_inputs_e2e, max_length=max_length)
    item["argument_extraction_pipeline_e2e"].update({
        "inputs": ae_inputs_e2e,
        "references": ae_refs_e2e,
        "predictions": ae_predictions_e2e,
    })
    
    # Argument Extraction based on merged TC results
    if len(event_detection_item.get("trigger_classification_merged", [])) > 0:
        ae_inputs_merged: List[str] = []
        ae_predictions_merged: List[str] = []
        ae_refs_merged: List[str] = []
        tc_pairs_merged = event_detection_item.get("trigger_classification_merged", [])
        for trigger_idx, (_trigger_text, _event_type, _) in enumerate(tc_pairs_merged):
            ae_input_merged = build_argument_extraction_input(ds_key, plain_text, _trigger_text, _event_type)
            if ae_input_merged:
                ae_inputs_merged.append(ae_input_merged)
        if ae_inputs_merged:
            ae_predictions_merged = batch_predict(model, tokenizer, ae_inputs_merged, max_length=max_length)
        item["argument_extraction_pipeline_merged"] = {
            "inputs": ae_inputs_merged,
            "references": ae_refs_merged,
            "predictions": ae_predictions_merged,
        } 
    return item

def run_single_inference_event_extraction_e2e(
    doc_id,
    tokenizer,
    model,
    ds_key: str,
    plain_text: str,
    max_length: int = 512,
    ) -> Dict:
    item: Dict = {
        "doc_id": doc_id,
        "source": plain_text,
        "event_extraction_e2e": {},
    }

    # Event Extraction E2E
    e2e_input = build_event_extraction_e2e_input(ds_key, plain_text)
    item["event_extraction_e2e"].update({"input": e2e_input, "reference": ""})
    e2e_pred = predict(model, tokenizer, e2e_input, max_length=max_length)
    if isinstance(e2e_pred, list):
        e2e_pred = e2e_pred[0] if e2e_pred else ""
    item["event_extraction_e2e"].update({"prediction": e2e_pred})

    return item

def parse_trigger_identification_classification(
    source: str,
    trigger_classification_pred: str
) -> List[Dict]:
    """
    Parse trigger classification pipeline output into structured triggers.
    
    Args:
        source: Original source text
        trigger_classification_pred: Output from trigger classification model with '=' mappings
            Example: 'reports=Statement | transferred=Sending'
    
    Returns:
        List of trigger dicts with 'text', 'type', and 'offset' keys.
        Example: [
            {'text': 'reports', 'type': 'Statement', 'offset': [18, 24]},
            {'text': 'transferred', 'type': 'Sending', 'offset': [44, 54]}
        ]
    """
    if not trigger_classification_pred:
        return []
    
    # Parse trigger classification output to get trigger-type pairs
    # Pattern: 'trigger_name=Type | trigger_name2=Type2' or 'reports=Statement | transferred=Sending'
    tc_pairs = []
    
    # Try pattern with 'trigger> text>=type' prefix first
    for m in re.finditer(r"trigger>\s*(.+?)\s*>=\s*([^|]+)", trigger_classification_pred):
        trigger_text = _clean(m.group(1))
        trigger_type = _clean(m.group(2))
        tc_pairs.append((trigger_text, trigger_type))
    
    # If no matches with 'trigger>' prefix, try simpler pattern (word=Type | word=Type)
    if not tc_pairs:
        for part in re.split(r"\s*\|\s*", trigger_classification_pred):
            part = part.strip()
            if '=' in part:
                trigger_text, trigger_type = part.split('=', 1)
                trigger_text = _clean(trigger_text)
                trigger_type = _clean(trigger_type)
                if trigger_text:  # Only add non-empty trigger texts
                    tc_pairs.append((trigger_text, trigger_type))
    
    if not tc_pairs:
        return []
    
    # Match triggers with their types and find offsets in source
    triggers = []
    search_start_idx = 0  # Track position in source for handling duplicate triggers
    
    for trigger_text, trigger_type in tc_pairs:
        # Add spaces around punctuation to match model preprocessing
        trigger_text_spaced = add_space_around_punctuation(trigger_text)
        
        # Find offset in original source text, handling duplicate trigger words
        # For single-word triggers, use word boundary search; for multi-word, use substring search
        if ' ' in trigger_text_spaced:
            # Multi-word trigger: use substring search from search_start_idx
            offset_start = source.find(trigger_text_spaced, search_start_idx)
        else:
            # Single-word trigger: use word boundary search to avoid substring matches
            offset_start = find_word_position(source, trigger_text_spaced, search_start_idx)
        
        if offset_start >= 0:
            offset_end = offset_start + len(trigger_text_spaced) - 1
            offset = [offset_start, offset_end]
            # Update search position for next trigger
            search_start_idx = offset_end + 1
        else:
            offset = []
        
        triggers.append({
            'text': trigger_text_spaced,
            'type': trigger_type,
            'offset': offset
        })
    
    return triggers

def parse_argument_extraction(source: str, ae_pred: str, trigger_offset=None) -> List[Dict]:
    """
    Parse argument extraction prediction into structured arguments.
    
    Args:
        source: Original source text
        ae_pred: Argument extraction prediction string
            Example: 'trigger> reports>=Statement: None=Addressee | None=Medium | argument> that it has transferred uranium enrichment techniques to Iran>=Message | None=Speaker'
        trigger_offset: Optional [trigger_start, trigger_end] offset to help select closest argument occurrence
    
    Returns:
        List of argument dicts with 'text', 'role', and 'offset' keys.
        Example: [
            {'text': 'that it has transferred uranium enrichment techniques to Iran', 'role': 'Message', 'offset': [44, 105]},
            {'text': '', 'role': 'Addressee', 'offset': []},
            ...
        ]
    """
    if not ae_pred:
        return []
    
    # Extract the arguments part (after the ':' which separates trigger spec from arguments)
    if ':' in ae_pred:
        args_part = ae_pred.split(':', 1)[1].strip()
    else:
        args_part = ae_pred
    
    arguments = []
    
    # Split by '|' to get individual argument specifications
    parts = re.split(r'\s*\|\s*', args_part)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Parse each part to extract argument text and role
        # Pattern 1: 'argument> text>=Role'
        m = re.match(r'argument>\s*(.+?)\s*>=\s*(.+)', part)
        if m:
            arg_text = _clean(m.group(1))
            arg_role = _clean(m.group(2))
            
            # Add spaces around punctuation to match model preprocessing
            arg_text_spaced = add_space_around_punctuation(arg_text)
            
            # Find offset in source with fallback for multi-word arguments
            # For multi-word arguments: try exact match first, then progressively remove words from end
            # For single-word arguments: use word boundary search to avoid substring matches
            matched_text = arg_text_spaced  # Default to original text
            if ' ' in arg_text_spaced:
                # Multi-word argument: use fallback mechanism
                positions, matched_text = find_text_with_word_fallback(source, arg_text_spaced, trigger_offset)
                offset_start = select_closest_from_positions(positions, trigger_offset)
                # If fallback didn't find anything, try simple substring search
                if offset_start < 0:
                    offset_start = select_closest_offset(source, arg_text_spaced, trigger_offset, is_word_boundary=False)
                    matched_text = arg_text_spaced  # Reset to original if fallback failed
            else:
                # Single-word argument: use word boundary search to avoid substring matches
                offset_start = select_closest_offset(source, arg_text_spaced, trigger_offset, is_word_boundary=True)
            
            if offset_start >= 0:
                offset_end = offset_start + len(matched_text) - 1
                offset = [offset_start, offset_end]
            else:
                offset = []
            
            arguments.append({
                'text': matched_text,  # Use the actually matched text
                'role': arg_role,
                'offset': offset
            })
        else:
            # Pattern 2: 'None=Role' or other text=Role format
            m = re.match(r'(\S+?)\s*=\s*(.+)', part)
            if m:
                arg_text_or_none = _clean(m.group(1))
                arg_role = _clean(m.group(2))
                
                # If it's 'None', skip this entry (ignore it)
                if arg_text_or_none.lower() == 'none':
                    continue
                else:
                    # It might be a standalone text without 'argument>' prefix
                    # Add spaces around punctuation to match model preprocessing
                    arg_text_spaced = add_space_around_punctuation(arg_text_or_none)
                    
                    # Find offset in source with fallback for multi-word arguments
                    # For multi-word arguments: try exact match first, then progressively remove words from end
                    # For single-word arguments: use word boundary search to avoid substring matches
                    matched_text = arg_text_spaced  # Default to original text
                    if ' ' in arg_text_spaced:
                        # Multi-word argument: use fallback mechanism
                        positions, matched_text = find_text_with_word_fallback(source, arg_text_spaced, trigger_offset)
                        offset_start = select_closest_from_positions(positions, trigger_offset)
                        # If fallback didn't find anything, try simple substring search
                        if offset_start < 0:
                            offset_start = select_closest_offset(source, arg_text_spaced, trigger_offset, is_word_boundary=False)
                            matched_text = arg_text_spaced  # Reset to original if fallback failed
                    else:
                        # Single-word argument: use word boundary search to avoid substring matches
                        offset_start = select_closest_offset(source, arg_text_spaced, trigger_offset, is_word_boundary=True)
                    
                    if offset_start >= 0:
                        offset_end = offset_start + len(matched_text) - 1
                        offset = [offset_start, offset_end]
                    else:
                        offset = []
                    
                    arguments.append({
                        'text': matched_text,  # Use the actually matched text
                        'role': arg_role,
                        'offset': offset
                    })
    
    return arguments

def parse_e2e_event_extraction_predictions(source: str, e2e_pred: str) -> List[Dict]:
    """
    Parse end-to-end event extraction predictions into structured events.
    
    Args:
        source: Original source text
        e2e_pred: E2E prediction string
            Example: 'trigger>reports>=Statement | argument>that it has transferred...>=Message || trigger>transferred>=Sending | argument>it>=Sender'
    
    Returns:
        List of event dicts with 'trigger' and 'arguments' keys.
        Example: [
            {
                'trigger': {'text': 'reports', 'type': 'Statement', 'offset': [18, 24]},
                'arguments': [{'text': 'that it has transferred...', 'role': 'Message', 'offset': [26, 89]}]
            },
            ...
        ]
    """
    if not e2e_pred:
        return []
    
    events = []
    
    # Split by '||' to get individual events
    event_groups = e2e_pred.split('||')
    
    search_start_idx = 0  # Track position for finding triggers sequentially
    
    for event_group in event_groups:
        event_group = event_group.strip()
        if not event_group:
            continue
        
        # Split by '|' to get trigger and arguments within the event
        components = [comp.strip() for comp in event_group.split('|')]
        
        event_data = {
            'trigger': None,
            'arguments': []
        }
        
        for comp in components:
            if not comp:
                continue
            
            # Parse trigger: 'trigger>text>=Type'
            if 'trigger>' in comp:
                m = re.match(r'trigger>\s*(.+?)\s*>=\s*(.+)', comp)
                if m:
                    trigger_text = _clean(m.group(1))
                    trigger_type = _clean(m.group(2))
                    
                    # Find offset in source - search from search_start_idx for sequential triggers
                    # For single-word triggers, use word boundary search; for multi-word, use substring search
                    if ' ' in trigger_text:
                        # Multi-word trigger: use substring search from search_start_idx
                        offset_start = source.find(trigger_text, search_start_idx)
                    else:
                        # Single-word trigger: use word boundary search to avoid substring matches
                        offset_start = find_word_position(source, trigger_text, search_start_idx)
                    
                    if offset_start >= 0:
                        offset_end = offset_start + len(trigger_text) - 1
                        offset = [offset_start, offset_end]
                        search_start_idx = offset_end + 1
                    else:
                        offset = []
                    
                    event_data['trigger'] = {
                        'text': trigger_text,
                        'type': trigger_type,
                        'offset': offset
                    }
            
            # Parse argument: 'argument>text>=Role'
            elif 'argument>' in comp:
                m = re.match(r'argument>\s*(.+?)\s*>=\s*(.+)', comp)
                if m:
                    arg_text = _clean(m.group(1))
                    arg_role = _clean(m.group(2))
                    
                    # Skip None placeholders
                    if arg_text.lower() == 'none':
                        continue
                    
                    # Find offset in source, selecting closest to trigger if available
                    # For multi-word arguments, use fallback mechanism; for single-word, use word boundary search
                    trigger_offset = event_data['trigger']['offset'] if event_data['trigger'] and event_data['trigger'].get('offset') else None
                    
                    matched_text = arg_text  # Default to original text
                    if ' ' in arg_text:
                        # Multi-word argument: use fallback mechanism
                        positions, matched_text = find_text_with_word_fallback(source, arg_text, trigger_offset)
                        offset_start = select_closest_from_positions(positions, trigger_offset)
                        # If fallback didn't find anything, try simple substring search
                        if offset_start < 0:
                            offset_start = select_closest_offset(source, arg_text, trigger_offset, is_word_boundary=False)
                            matched_text = arg_text  # Reset to original if fallback failed
                    else:
                        # Single word argument: use word boundary search to avoid substring matches
                        offset_start = select_closest_offset(source, arg_text, trigger_offset, is_word_boundary=True)
                    
                    if offset_start >= 0:
                        offset_end = offset_start + len(matched_text) - 1
                        offset = [offset_start, offset_end]
                    else:
                        offset = []
                    
                    event_data['arguments'].append({
                        'text': matched_text,  # Use the actually matched text
                        'role': arg_role,
                        'offset': offset
                    })
        
        # Only add event if it has a valid trigger
        if event_data['trigger']:
            events.append(event_data)
    
    return events

def structure_argument_extraction_pipeline_predictions(item: Dict, triggers_results: List[Dict], argument_extraction_task_name: str) -> Dict:
    """
    Parse pipeline predictions into structured event format.
    
    Extracts and structures:
    - Triggers from trigger_identification + trigger_classification_pipeline
    - Arguments from argument_extraction_pipeline_pipeline
    """
    source = item.get("source", "")
    parsed = {
        "doc_id": item.get("doc_id", ""),
        "source": source,
        "events": []
    }
    
   
    # Parse arguments from argument_extraction_pipeline_pipeline
    arg_preds = item.get(argument_extraction_task_name, {}).get("predictions", [])
    events = []
    for i, trigger in enumerate(triggers_results):
        trigger_dict = {
            "text": trigger[0] if len(trigger) > 0 else "",
            "type": trigger[1] if len(trigger) > 1 else "",
            "offset": trigger[2] if len(trigger) > 2 else [],
        }

        if i < len(arg_preds):
            # Pass trigger offset to select closest argument occurrence
            trigger_offset = trigger_dict.get('offset') if trigger_dict.get('offset') else None
            arguments = parse_argument_extraction(source, arg_preds[i], trigger_offset=trigger_offset)
        else:
            arguments = []

        events.append({
            "trigger": trigger_dict,
            "arguments": arguments,
        })
    parsed["events"] = events
    return parsed

def structure_e2e_pipeline_predictions(item: Dict, triggers_e2e: List[Dict]) -> Dict:
    """
    Parse end-to-end trigger classification and argument extraction predictions into structured event format.
    """
    source = item.get("source", "")
    parsed = {
        "doc_id": item.get("doc_id", ""),
        "source": source,
        "events": []
    }
    
    # Parse arguments from argument_extraction_pipeline_e2e
    arg_preds_e2e = item.get("argument_extraction_pipeline_e2e", {}).get("predictions", [])
    events = []
    for i, trigger in enumerate(triggers_e2e):
        trigger_dict = {
            "text": trigger[0] if len(trigger) > 0 else "",
            "type": trigger[1] if len(trigger) > 1 else "",
            "offset": trigger[2] if len(trigger) > 2 else [],
        }

        if i < len(arg_preds_e2e):
            # Pass trigger offset to select closest argument occurrence
            trigger_offset = trigger_dict.get('offset') if trigger_dict.get('offset') else None
            arguments = parse_argument_extraction(source, arg_preds_e2e[i], trigger_offset=trigger_offset)
        else:
            arguments = []

        events.append({
            "trigger": trigger_dict,
            "arguments": arguments,
        })

    parsed["events"] = events
    return parsed

def present_parsed_output(item: Dict) -> Dict:
    """Return parsed end-to-end events for a single item."""
    source = item.get("source", "")
    parsed_e2e = {
        "doc_id": item.get("doc_id", ""),
        "source": source,
        "events": parse_e2e_event_extraction_predictions(
            source,
            item.get("event_extraction_e2e", {}).get("prediction", ""),
        ),
    }
    return parsed_e2e





def main(doc_id: str, tokenizer_dir: str, model_dir: str, domain: str, text: str, max_length: int):
    # run single-sample inference from command line
    model, tokenizer = construct_t5_model(
        tokenizer_dir=tokenizer_dir,
        model_dir=model_dir)
    # Stage 1: Event Detection (TI + TC)
    event_detection_item = run_single_inference_event_detection(
        doc_id=doc_id,
        tokenizer=tokenizer,
        model=model,
        ds_key=domain,
        plain_text=text,
        max_length=max_length,
    )
    parsed_event_detection = parse_and_merge_single_inference_event_detection_results(event_detection_item)
    #print('Parsed Event Detection Results: ', json.dumps(parsed_event_detection, indent=2))
    
    # Stage 2: Argument Extraction 
    argument_extraction_item = run_single_inference_event_argument_extraction(
        tokenizer=tokenizer,
        model=model,
        ds_key=domain,
        plain_text=text,
        event_detection_item=parsed_event_detection,
        max_length=max_length,
    )
    
    parsed_argument_extractions_pipeline = structure_argument_extraction_pipeline_predictions(
        argument_extraction_item,
        parsed_event_detection.get("trigger_classification_pipeline", []),
        "argument_extraction_pipeline_pipeline",
    )
    parsed_argument_extraction_e2e = structure_argument_extraction_pipeline_predictions(
        argument_extraction_item,
        parsed_event_detection.get("trigger_classification_e2e", []),
        "argument_extraction_pipeline_e2e",
    )
    parsed_argument_extraction_merged = structure_argument_extraction_pipeline_predictions(
        argument_extraction_item,
        parsed_event_detection.get("trigger_classification_merged", []),
        "argument_extraction_pipeline_merged",
    ) if len(parsed_event_detection.get("trigger_classification_merged", [])) > 0 else {}

    #print('Parsed Argument Extraction Results (Pipeline): ', json.dumps(parsed_argument_extractions_pipeline, indent=2))
    #print('Parsed Argument Extraction Results (E2E): ', json.dumps(parsed_argument_extraction_e2e, indent=2))
    #if parsed_argument_extraction_merged:
        #print('Parsed Argument Extraction Results (Merged): ', json.dumps(parsed_argument_extraction_merged, indent=2))
    #    pass
    # parallel to pipeline of stage one + stage two.  Event Extraction End-to-End
    event_extraction_e2e_item = run_single_inference_event_extraction_e2e(
        doc_id=doc_id,
        tokenizer=tokenizer,
        model=model,
        ds_key=domain,
        plain_text=text,
        max_length=max_length,
    )
    
    parsed_event_extraction_e2e = parse_e2e_event_extraction_predictions(
        text,
        event_extraction_e2e_item.get("event_extraction_e2e", {}).get("prediction", ""),
    )
    #print('Parsed Event Extraction E2E Results: ', json.dumps(
    #    parsed_event_extraction_e2e,
    #    indent=2,
    #))

    # Structure all results and return
    structured_results = {
        "doc_id": doc_id,
        "source": text,
        "argument_extraction_pipeline": parsed_argument_extractions_pipeline['events'] if parsed_argument_extractions_pipeline else [],
        "argument_extraction_e2e": parsed_argument_extraction_e2e['events'] if parsed_argument_extraction_e2e else [],
        "argument_extraction_merged": parsed_argument_extraction_merged if parsed_argument_extraction_merged else {},
        "event_extraction_e2e": parsed_event_extraction_e2e,
    }
    return structured_results
    
if __name__ == "__main__":
    # test run single inference and parse predictions
    doc_id = "01"
    text = "Argentina rejects reports that it has transferred uranium enrichment techniques to Iran (2958)."
    #model_dir = "/nfs/work/debi5729/google-t5-t5-base_split1_geneva_wikievents_casie_genia2013_m2e2_rams_amount_1_e2e_True_full_latest_expressive_prompt"
    model_dir = "/nfs/work/debi5729/google-t5-t5-base_split1_geneva_amount_1_e2e_True_full_latest_expressive_prompt"
    tokenizer_dir = "google-t5/t5-base"
    ds_key = "geneva"
    text_path = "/nfs/work/debi5729/pipeline_for_VCR/m2e2_annotations/text_only_event.json"
    text_data = json.load(open(text_path, "r"))
    results = []
    save_path = "/nfs/work/debi5729/pipeline_for_VCR/m2e2_annotations/structured_event_extraction_results.json"
    for d in text_data:
        doc_id = d['sentence_id']
        text = d['sentence']
        print('Running inference for doc_id: ', doc_id)
        structured_results = main(
        doc_id=doc_id,
        tokenizer_dir=tokenizer_dir,
        model_dir=model_dir,
        domain=ds_key,
        text=text,
        max_length=512,
        )
        results.append(structured_results)
        #save_path = "/nfs/work/debi5729/pipeline_for_VCR/m2e2_annotations/structured_event_extraction_results.json"
        with open(save_path, "w") as f:
            json.dump(results, f, indent=2)
    with open(save_path, "w") as f:
            json.dump(results, f, indent=2)
    # test parse functions
    #print(json.dumps(structured_results, indent=2))
    