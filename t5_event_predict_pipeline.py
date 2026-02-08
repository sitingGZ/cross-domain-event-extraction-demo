"""
Pipeline prediction module for T5-based event extraction using expressive prompts.

This module chains predictions across three tasks:
1. Trigger Identification - identifies trigger spans
2. Trigger Classification Pipeline - classifies triggers (uses TI output)
3. Argument Extraction Pipeline - extracts arguments (uses TC output)

For samples where TC produces no parseable results, falls back to:
- Event Extraction E2E task
"""

from __future__ import annotations
from typing import List, Dict, Tuple
import json
import os
from collections import defaultdict

from transformers import T5ForConditionalGeneration, AutoTokenizer
from parse_task_outputs import (
    parse_triggers_from_tagged,
    parse_tc_pairs,
    parse_argument_extraction_pipeline_predictions
)
from t5_event_predict import (
    predict,
    batch_predict,
    load_dataset_to_predict_trigger_identification,
    load_dataset_to_predict_trigger_classification_pipeline,
    load_dataset_to_predict_trigger_classification_e2e,
    load_dataset_to_predict_argument_extraction_pipeline,
    load_dataset_to_predict_event_extraction_e2e
)
from pattern_tagprime import event_type_tags,patterns, role_type_tags


def build_trigger_classification_input_pipeline(ds_key: str, ti_prediction: str) -> str:
    """
    Build trigger classification input from trigger identification prediction.
    
    The TI prediction already contains the full text with trigger> markers,
    so we just wrap it in the TC task prompt format.
    
    Args:
        ds_key: dataset key (e.g., "m2e2", "geneva")
        ti_prediction: model output from trigger identification task
    
    Returns:
        Input string for trigger classification pipeline task
    """
    return f"Domain: {ds_key}. Classify trigger types. {ti_prediction}"

def build_trigger_classification_input_e2e(ds_key: str, plain_text: str) -> str:
    """
    Build trigger classification input with trigger classification e2e prompt.
    
    The E2E prediction already contains the full text with trigger> markers,
    so we just wrap it in the TC task prompt format.
    
    Args:
        ds_key: dataset key (e.g., "m2e2", "geneva")
        plain_text: plain text input
    Returns:
        Input string for trigger classification e2e task
    """
    return f"Domain: {ds_key}. Classify trigger types end-to-end. {plain_text}"

def build_argument_extraction_input(
    ds_key: str,
    original_text: str,
    tc_prediction: str,
    trigger_idx: int = 0
) -> str:
    """
    Build argument extraction input for a specific trigger from TC prediction.
    """
    tc_pairs, _, _ = parse_tc_pairs(ds_key, tc_prediction)
    if not tc_pairs:
        return ""
    if trigger_idx >= len(tc_pairs):
        trigger_idx = 0
    trigger_text, event_type = tc_pairs[trigger_idx]
    
    # Get roles for this event type using role_type_tags first, then patterns fallback
    roles = role_type_tags.get(ds_key, {}).get(event_type, [])
    if not roles:
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
        print(f"  Available keys in role_type_tags[{ds_key}]: {list(role_type_tags.get(ds_key, {}).keys())[:5]}...")
    
    # If roles_str is empty, still generate the input but note the missing roles
    return (
        f"Domain: {ds_key}. Extract arguments for a specific event. "
        f"argument> {roles_str} for trigger> {trigger_text}>={event_type}: {original_text}"
    )



def run_pipeline_prediction(
    tokenizer_dir: str,
    model_dir: str,
    ds_key: str,
    split: str = "test",
    batch_size: int = 8,
    max_length: int = 512,
    output_dir: str = None
) -> List[Dict]:
    """
    Run chained pipeline predictions across three tasks.
    
    For samples where TC produces no results, saves them for fallback to E2E task.
    
    Args:
        model_dir: directory containing the trained T5 model
        ds_key: dataset key
        split: "test" or "val"
        batch_size: batch size for prediction
        max_length: max length for generation
        output_dir: directory to save results (default: model_dir/pipeline_predictions)
    
    Returns:
        List of items, one per doc_id, including inputs, references, and predictions for each task
    """
    
    if output_dir is None:
        output_dir = os.path.join(model_dir, "pipeline_predictions")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load model and tokenizer
    print(f"Loading model from {model_dir}...")
    model = T5ForConditionalGeneration.from_pretrained(model_dir)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
    device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    
    main_root = "/nfs/data/debi5729/processed_data"
    
    # Define splits mapping
    splits_map = {
        "test": "test.json",
        "val": "dev.json"
    }
    
    # Load datasets
    print(f"Loading datasets for {ds_key} {split}...")
    val_ti, test_ti = load_dataset_to_predict_trigger_identification(main_root, ds_key, splits=splits_map)
    val_tc, test_tc = load_dataset_to_predict_trigger_classification_pipeline(main_root, ds_key, splits=splits_map)
    val_tc_e2e, test_tc_e2e = load_dataset_to_predict_trigger_classification_e2e(main_root, ds_key, splits=splits_map)
    val_ae, test_ae = load_dataset_to_predict_argument_extraction_pipeline(main_root, ds_key, splits=splits_map)
    val_e2e, test_e2e = load_dataset_to_predict_event_extraction_e2e(main_root, ds_key, splits=splits_map)
    
    # Select the appropriate split
    ti_test = test_ti if split == "test" else val_ti
    tc_test = test_tc if split == "test" else val_tc
    tc_test_e2e = test_tc_e2e if split == "test" else val_tc_e2e
    ae_test = test_ae if split == "test" else val_ae
    e2e_test = test_e2e if split == "test" else val_e2e

    # Organize data by doc_id
    ti_by_doc = {rec['doc_id']: rec for rec in ti_test}
    tc_ref_by_doc = {rec['doc_id']: rec.get('output', '') for rec in tc_test}
    tc_test_e2e_by_doc = {rec['doc_id']: rec for rec in tc_test_e2e}
    ae_refs_by_doc = defaultdict(list)
    for rec in ae_test:
        ae_refs_by_doc[rec['doc_id']].append(rec.get('output', ''))
    e2e_by_doc = {rec['doc_id']: rec for rec in e2e_test}

    def extract_plain_text(source: str) -> str:
        parts = source.split('. ', 2)
        return parts[2] if len(parts) >= 3 else source

    doc_ids = list(ti_by_doc.keys())
    results: List[Dict] = []

    print(f"\n{'='*80}")
    print("Running pipeline by doc_id...")
    print(f"{'='*80}")

    for doc_id in doc_ids:
        try:
            item = {
                'doc_id': doc_id,
                'source': extract_plain_text(ti_by_doc[doc_id]['input']) if doc_id in ti_by_doc else '',
                'trigger_identification': {},
                'trigger_classification_pipeline': {},
                'trigger_classification_e2e': {},
                'argument_extraction_pipeline_pipeline': {},
                'argument_extraction_pipeline_e2e': {},
                'event_extraction_e2e': {}
            }

            # Trigger Identification
            ti_rec = ti_by_doc.get(doc_id)
            ti_pred = ''
            if ti_rec:
                ti_input = ti_rec['input']
                ti_ref = ti_rec.get('output', '')
                item['trigger_identification'].update({'input': ti_input, 'reference': ti_ref})
                ti_pred = predict(model, tokenizer, ti_input, max_length=max_length)
                if isinstance(ti_pred, list):
                    ti_pred = ti_pred[0] if ti_pred else ''
                item['trigger_identification'].update({'prediction': ti_pred})

            # Trigger Classification Pipeline
            tc_input = build_trigger_classification_input_pipeline(ds_key, ti_pred) if ti_pred else ''
            tc_ref = tc_ref_by_doc.get(doc_id, '')
            item['trigger_classification_pipeline'].update({'input': tc_input, 'reference': tc_ref})
            tc_pred = predict(model, tokenizer, tc_input, max_length=max_length) if tc_input else ''
            if isinstance(tc_pred, list):
                tc_pred = tc_pred[0] if tc_pred else ''
            item['trigger_classification_pipeline'].update({'prediction': tc_pred})
            
            # Trigger Classification E2E
            tc_rec_e2e = tc_test_e2e_by_doc.get(doc_id)
            tc_e2e_ref = tc_rec_e2e.get('output', '') if tc_rec_e2e else ''
            tc_input_e2e = tc_rec_e2e.get('input', '') if tc_rec_e2e else ''
            item['trigger_classification_e2e'].update({'input': tc_input_e2e, 'reference': tc_e2e_ref})
            tc_pred_e2e = predict(model, tokenizer, tc_input_e2e, max_length=max_length) if tc_input_e2e else ''
            if isinstance(tc_pred_e2e, list):
                tc_pred_e2e = tc_pred_e2e[0] if tc_pred_e2e else ''
            item['trigger_classification_e2e'].update({'prediction': tc_pred_e2e    })

            # Argument Extraction Pipeline  pipeline after trigger classification pipeline(list of inputs/preds/refs)
            ae_inputs: List[str] = []
            ae_predictions: List[str] = []
            ae_references: List[str] = ae_refs_by_doc.get(doc_id, [])

            if tc_pred and isinstance(tc_pred, str):
                original_text = item['source']
                tc_pairs, _, _ = parse_tc_pairs(ds_key, tc_pred)
                for trigger_idx, (trigger_text, event_type) in enumerate(tc_pairs):
                    ae_input = build_argument_extraction_input(ds_key, original_text, tc_pred, trigger_idx)
                    if ae_input:
                        ae_inputs.append(ae_input)

            if ae_inputs:
                ae_predictions = batch_predict(model, tokenizer, ae_inputs, max_length=max_length)

            item['argument_extraction_pipeline_pipeline'].update({
                'inputs': ae_inputs,
                'references': ae_references,
                'predictions': ae_predictions
            })
            # Argument Extraction Pipeline  e2e after trigger classification e2e (list of inputs/preds/refs)
            ae_inputs_e2e: List[str] = []
            ae_predictions_e2e: List[str] = []
            ae_references_e2e: List[str] = ae_refs_by_doc.get(doc_id, [])
            if tc_pred_e2e and isinstance(tc_pred_e2e, str):
                original_text = item['source']
                tc_pairs_e2e, _, _ = parse_tc_pairs(ds_key, tc_pred_e2e)
                for trigger_idx, (trigger_text, event_type) in enumerate(tc_pairs_e2e):
                    ae_input_e2e = build_argument_extraction_input(ds_key, original_text, tc_pred_e2e, trigger_idx)
                    if ae_input_e2e:
                        ae_inputs_e2e.append(ae_input_e2e)  
            if ae_inputs_e2e:
                ae_predictions_e2e = batch_predict(model, tokenizer, ae_inputs_e2e, max_length=max_length)
            item['argument_extraction_pipeline_e2e'].update({
                'inputs': ae_inputs_e2e,
                'references': ae_references_e2e,
                'predictions': ae_predictions_e2e
            })
            
            # Event Extraction E2E
            e2e_rec = e2e_by_doc.get(doc_id)
            if e2e_rec:
                e2e_input = e2e_rec.get('input', '')
                e2e_ref = e2e_rec.get('output', '')
                item['event_extraction_e2e'].update({'input': e2e_input, 'reference': e2e_ref})
                e2e_pred = predict(model, tokenizer, e2e_input, max_length=max_length) if e2e_input else ''
                if isinstance(e2e_pred, list):
                    e2e_pred = e2e_pred[0] if e2e_pred else ''
                item['event_extraction_e2e'].update({'prediction': e2e_pred})

            results.append(item)
        except Exception as e:
            print(f"Error processing doc_id {doc_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save results
    output_file = os.path.join(output_dir, f"pipeline_and_e2e_predictions_{split}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print("Pipeline prediction complete!")
    print(f"Results saved to {output_file}")
    print(f"{'='*80}")
    print(f"Processed {len(results)} documents.")

    return results


if __name__ == "__main__":
    import argparse
    
    datasets = ['rams']
    #datasets = ["geneva", "wikievents", "casie", "genia2013", "m2e2", "rams"]
    tokenizer_dir = "google-t5/t5-base"
    amount = 1
    model_dir = f"/nfs/work/debi5729/google-t5-t5-base_split1_{'_'.join(datasets)}_amount_{amount}_e2e_True_full_latest_expressive_prompt"
    epochs = [40]
    split = "test"
    batch_size = 8
    # Process each epoch
    ds_keys = [ 'rams']
    for ds_key in ds_keys:
        for epoch in epochs:
            epoch_dir = os.path.join(model_dir, f"checkpoint-epoch-{epoch}")
            output_dir = os.path.join(model_dir, "generations", f"epoch-{epoch}", ds_key)
        
            print(f"\n{'='*80}")
            print(f"Processing epoch {epoch}")
            print(f"Checkpoint: {epoch_dir}")
            print(f"Output: {output_dir}")
            print(f"{'='*80}")
        
            if not os.path.exists(epoch_dir):
                print(f"Warning: Checkpoint directory not found: {epoch_dir}")
                continue
        
            try:
                results = run_pipeline_prediction(
                    tokenizer_dir=tokenizer_dir,
                    model_dir=epoch_dir,
                    ds_key=ds_key,
                    split=split,
                    batch_size=batch_size,
                    max_length=512,
                    output_dir=output_dir
                )
                print(f"Successfully saved results for epoch {epoch}")
            except Exception as e:
                print(f"Error processing epoch {epoch}: {e}")
            