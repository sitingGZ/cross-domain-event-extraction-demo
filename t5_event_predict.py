"""
Prediction module for T5-based event extraction using expressive prompts.

This module provides functions to load datasets for prediction across different tasks
following the expressive prompt pattern:
- trigger_identification
- trigger_classification_pipeline
- trigger_classification_e2e
- argument_identification_e2e
- argument_extraction_pipeline
- event_extraction_e2e
"""

from __future__ import annotations
from typing import Iterable, Dict, List

import argparse
from transformers import AutoTokenizer, T5ForConditionalGeneration, TrainingArguments, Trainer, DataCollatorForSeq2Seq, TrainerCallback
import torch
from event_extraction_task_annotation_expressive_prompt import (
    get_dataset_instances_no_index, 
    get_dataset_instances_no_index_e2e,
    get_dataset_instances_no_index_all
)
import os
from t5_event_train import TokenizedEventDataset
import json


def predict(
    model: T5ForConditionalGeneration,
    tokenizer,
    source_text: str,
    max_length: int = 512,
    num_return_sequences: int = 1,
    num_beams: int = 5,
    top_k: int = 50,
    top_p: float = 0.95,
    do_sample: bool = False,
    repetition_penalty: float = 2.5,
    length_penalty: float = 1.0,
    early_stopping: bool = True,
    skip_special_tokens: bool = True,
    clean_up_tokenization_spaces: bool = True,
) -> list[str]:
    """Predict on a single source text."""
    return batch_predict(
        model,
        tokenizer,
        [source_text],
        max_length=max_length,
        num_return_sequences=num_return_sequences,
        num_beams=num_beams,
        top_k=top_k,
        top_p=top_p,
        do_sample=do_sample,
        repetition_penalty=repetition_penalty,
        length_penalty=length_penalty,
        early_stopping=early_stopping,
        skip_special_tokens=skip_special_tokens,
        clean_up_tokenization_spaces=clean_up_tokenization_spaces,
    )


def batch_predict(
    model: T5ForConditionalGeneration,
    tokenizer,
    source_texts: Iterable[str],
    max_length: int = 512,
    num_return_sequences: int = 1,
    num_beams: int = 5,
    top_k: int = 50,
    top_p: float = 0.95,
    do_sample: bool = False,
    repetition_penalty: float = 2.5,
    length_penalty: float = 1.0,
    early_stopping: bool = True,
    skip_special_tokens: bool = True,
    clean_up_tokenization_spaces: bool = True,
) -> list[str]:
    """Predict on a batch of source texts."""
    input_encoding = tokenizer(
        source_texts,
        padding="longest",
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
    )
    return predict_on_ids(
        model,
        tokenizer,
        input_ids=input_encoding.input_ids,
        attention_mask=input_encoding.attention_mask,
        max_length=max_length,
        num_return_sequences=num_return_sequences,
        num_beams=num_beams,
        top_k=top_k,
        top_p=top_p,
        do_sample=do_sample,
        repetition_penalty=repetition_penalty,
        length_penalty=length_penalty,
        early_stopping=early_stopping,
        skip_special_tokens=skip_special_tokens,
        clean_up_tokenization_spaces=clean_up_tokenization_spaces,
    )


def predict_on_ids(
    model: T5ForConditionalGeneration,
    tokenizer,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    max_length: int = 512,
    num_return_sequences: int = 1,
    num_beams: int = 5,
    top_k: int = 50,
    top_p: float = 0.95,
    do_sample: bool = False,
    repetition_penalty: float = 2.5,
    length_penalty: float = 1.0,
    early_stopping: bool = True,
    skip_special_tokens: bool = True,
    clean_up_tokenization_spaces: bool = True,
    debug: bool = False,
) -> list[str]:
    """Predict on pre-tokenized input IDs."""
    generate_kwargs = {
        'input_ids': input_ids.to(model.device),
        'attention_mask': attention_mask.to(model.device),
        'max_length': max_length,
        'num_return_sequences': num_return_sequences,
        'length_penalty': length_penalty,
        'early_stopping': early_stopping,
        'repetition_penalty': repetition_penalty,
    }
    # Use beams when not sampling; use sampling params only when do_sample=True
    if do_sample:
        generate_kwargs.update({'do_sample': True, 'top_p': top_p, 'top_k': top_k, 'num_beams': None})
    else:
        generate_kwargs.update({'do_sample': False, 'num_beams': num_beams})

    generated_ids = model.generate(**generate_kwargs)
    if debug:
        print(f"Generated shape: {generated_ids.shape}")
        print(f"First 3 sequences (token IDs): {[generated_ids[i].tolist() for i in range(min(3, generated_ids.size(0)))]}")
    preds = []
    for generated_id in generated_ids:
        if debug:
            print("Decoded (skip_special_tokens=False):",
                  tokenizer.decode(generated_id, skip_special_tokens=False, clean_up_tokenization_spaces=False))
        decoded = tokenizer.decode(
            generated_id,
            skip_special_tokens=skip_special_tokens,
            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
        )
        preds.append(decoded)
    return preds


def task_generation(batch_items, model, tokenizer):
    """Generate predictions for a batch of items."""
    batch_enc = tokenizer(batch_items, return_tensors='pt', max_length=512, return_attention_mask=True, padding=True, truncation=True)
    batch_generation = predict_on_ids(
        model,
        tokenizer,
        input_ids=batch_enc['input_ids'].to(model.device),
        attention_mask=batch_enc['attention_mask'].to(model.device),
    )
    return batch_generation


# ============================================================================
# Dataset Loading Functions for Expressive Prompt Pattern
# ============================================================================

def load_dataset_to_predict_trigger_identification(main_root, ds_key, split_group="split1", splits=None):
    """Load dataset for trigger identification task (expressive prompts)."""
    val_records = {}
    test_records = {}
    
    instances = get_dataset_instances_no_index(main_root, ds_key, split_group=split_group, splits=splits)
    
    val_records = instances.get('trigger_identification', {}).get('val', [])
    test_records = instances.get('trigger_identification', {}).get('test', [])
    
    return val_records, test_records


def load_dataset_to_predict_trigger_classification_pipeline(main_root, ds_key, split_group="split1", splits=None):
    """Load dataset for trigger classification pipeline task (with tagged input)."""
    val_records = {}
    test_records = {}
    
    instances = get_dataset_instances_no_index(main_root, ds_key, split_group=split_group, splits=splits)
    
    val_records = instances.get('trigger_classification_pipeline', {}).get('val', [])
    test_records = instances.get('trigger_classification_pipeline', {}).get('test', [])
    
    return val_records, test_records


def load_dataset_to_predict_trigger_classification_e2e(main_root, ds_key, split_group="split1", splits=None):
    """Load dataset for end-to-end trigger classification task (plain text input)."""
    val_records = {}
    test_records = {}
    
    instances = get_dataset_instances_no_index(main_root, ds_key, split_group=split_group, splits=splits)
    
    val_records = instances.get('trigger_classification_e2e', {}).get('val', [])
    test_records = instances.get('trigger_classification_e2e', {}).get('test', [])
    
    return val_records, test_records


def load_dataset_to_predict_argument_identification_e2e(main_root, ds_key, split_group="split1", splits=None):
    """Load dataset for end-to-end argument identification task."""
    val_records = {}
    test_records = {}
    
    instances = get_dataset_instances_no_index(main_root, ds_key, split_group=split_group, splits=splits)
    
    val_records = instances.get('argument_identification_e2e', {}).get('val', [])
    test_records = instances.get('argument_identification_e2e', {}).get('test', [])
    
    return val_records, test_records


def load_dataset_to_predict_argument_extraction_pipeline(main_root, ds_key, split_group="split1", splits=None):
    """Load dataset for argument extraction pipeline task (per-event extraction)."""
    val_records = {}
    test_records = {}
    
    instances = get_dataset_instances_no_index(main_root, ds_key, split_group=split_group, splits=splits)
    
    val_records = instances.get('argument_extraction_pipeline', {}).get('val', [])
    test_records = instances.get('argument_extraction_pipeline', {}).get('test', [])
    
    return val_records, test_records


def load_dataset_to_predict_event_extraction_e2e(main_root, ds_key, split_group="split1", splits=None):
    """Load dataset for end-to-end event extraction task (triggers + arguments together)."""
    val_records = {}
    test_records = {}
    
    instances = get_dataset_instances_no_index_e2e(main_root, ds_key, split_group=split_group, splits=splits)
    
    val_records = instances.get('event_extraction_e2e', {}).get('val', [])
    test_records = instances.get('event_extraction_e2e', {}).get('test', [])
    
    return val_records, test_records


def load_dataset_to_predict_all_tasks(main_root, ds_key, split_group="split1", splits=None, include_e2e=True):
    """
    Load datasets for all tasks for a given dataset.
    
    Returns:
        Tuple of (val_records_by_task, test_records_by_task) where each is a dict
        mapping task names to lists of records.
    """
    val_records_by_task = {}
    test_records_by_task = {}
    
    # Load non-e2e tasks
    instances = get_dataset_instances_no_index(main_root, ds_key, split_group=split_group, splits=splits)
    
    # Trigger identification
    val_records_by_task['trigger_identification'] = instances.get('trigger_identification', {}).get('val', [])
    test_records_by_task['trigger_identification'] = instances.get('trigger_identification', {}).get('test', [])
    
    # Trigger classification (pipeline)
    val_records_by_task['trigger_classification_pipeline'] = instances.get('trigger_classification_pipeline', {}).get('val', [])
    test_records_by_task['trigger_classification_pipeline'] = instances.get('trigger_classification_pipeline', {}).get('test', [])
    
    # Trigger classification (e2e)
    val_records_by_task['trigger_classification_e2e'] = instances.get('trigger_classification_e2e', {}).get('val', [])
    test_records_by_task['trigger_classification_e2e'] = instances.get('trigger_classification_e2e', {}).get('test', [])
    
    # Argument identification (e2e)
    val_records_by_task['argument_identification_e2e'] = instances.get('argument_identification_e2e', {}).get('val', [])
    test_records_by_task['argument_identification_e2e'] = instances.get('argument_identification_e2e', {}).get('test', [])
    
    # Argument extraction (pipeline)
    val_records_by_task['argument_extraction_pipeline'] = instances.get('argument_extraction_pipeline', {}).get('val', [])
    test_records_by_task['argument_extraction_pipeline'] = instances.get('argument_extraction_pipeline', {}).get('test', [])
    
    # Load e2e event extraction if requested
    if include_e2e:
        e2e_instances = get_dataset_instances_no_index_e2e(main_root, ds_key, split_group=split_group, splits=splits)
        val_records_by_task['event_extraction_e2e'] = e2e_instances.get('event_extraction_e2e', {}).get('val', [])
        test_records_by_task['event_extraction_e2e'] = e2e_instances.get('event_extraction_e2e', {}).get('test', [])
    
    return val_records_by_task, test_records_by_task


def write_task_generation_to_file(epoch, ds_key, generations, samples, task, out_base, split="val"):
    """Write generation results to JSONL file."""
    for j, gen in enumerate(generations):
        src = samples[j].get('input')
        ref = samples[j].get('output')
        doc_id = samples[j].get('doc_id')
        
        rec = {
            'epoch': epoch,
            'dataset': ds_key,
            'doc_id': doc_id,
            'split': split,
            'task': task,
            'index': j,
            'source': src,
            'reference': ref,
            'prediction': gen,
        }
        out_file = os.path.join(out_base, f'{split}.jsonl')
        with open(out_file, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')


def main(datasets, epochs, tokenizer_model_dir, model_dir, tasks=None, debug=False, 
         include_e2e=True, split_group="split1", splits=None, batch_size=8):
    """
    Main prediction function for expressive prompt tasks.
    
    Args:
        datasets: List of dataset keys to predict on
        epochs: List of epoch numbers to load checkpoints from
        tokenizer_model_dir: Path or HF model ID for tokenizer
        model_dir: Base directory containing model checkpoints
        tasks: List of tasks to predict on. If None, uses all available tasks
        debug: Whether to print debug information
        include_e2e: Whether to include end-to-end event extraction task
        split_group: Split group name (default: "split1")
        splits: Dict mapping split names to file names
        batch_size: Batch size for prediction
    """
    main_root = "/nfs/data/debi5729/processed_data"
    
    if splits is None:
        splits = {"val": "dev.json", "test": "test.json"}
    
    # Default task list
    if tasks is None:
        tasks = [
            'trigger_identification',
            'trigger_classification_pipeline', 
            'trigger_classification_e2e',
            'argument_identification_e2e',
            'argument_extraction_pipeline'
        ]
        if include_e2e:
            tasks.append('event_extraction_e2e')
    
    for epoch in epochs:
        print(f"\n{'='*80}")
        print(f"Processing epoch: {epoch}")
        print(f"{'='*80}")
        
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_model_dir)
        model = T5ForConditionalGeneration.from_pretrained(os.path.join(model_dir, f"checkpoint-epoch-{epoch}"))
        
        # Move model to GPU if available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)
        print(f"Using device: {device}")
        
        for ds_key in datasets:
            print(f"\n{'─'*80}")
            print(f"Loading dataset: {ds_key}")
            print(f"{'─'*80}")
            
            # Load all datasets
            val_records_by_task, test_records_by_task = load_dataset_to_predict_all_tasks(
                main_root, ds_key, split_group=split_group, splits=splits, include_e2e=include_e2e
            )
            
            # Prepare output folder
            out_base = os.path.join(model_dir, 'generations', f'epoch-{epoch}', ds_key)
            os.makedirs(out_base, exist_ok=True)
            
            # Predict on validation set
            print(f"\nPredicting on validation set...")
            for task in tasks:
                samples = val_records_by_task.get(task, [])
                if not samples:
                    print(f"  Skipping {task}: no validation samples")
                    continue
                
                print(f"  Task: {task} ({len(samples)} samples)")
                
                for i in range(0, len(samples), batch_size):
                    batch_items = [samples[j].get('input') for j in range(i, min(i + batch_size, len(samples)))]
                    batch_enc = tokenizer(
                        batch_items, 
                        return_tensors='pt', 
                        max_length=512, 
                        return_attention_mask=True, 
                        padding=True, 
                        truncation=True
                    )
                    batch_generation = predict_on_ids(
                        model,
                        tokenizer,
                        input_ids=batch_enc['input_ids'].to(device),
                        attention_mask=batch_enc['attention_mask'].to(device),
                        debug=debug
                    )
                    
                    for j, gen in enumerate(batch_generation):
                        src = samples[i + j].get('input')
                        ref = samples[i + j].get('output')
                        doc_id = samples[i + j].get('doc_id')
                        
                        rec = {
                            'epoch': epoch,
                            'dataset': ds_key,
                            'doc_id': doc_id,
                            'split': 'val',
                            'task': task,
                            'index': i + j,
                            'source': src,
                            'reference': ref,
                            'prediction': gen,
                        }
                        out_file = os.path.join(out_base, 'val.jsonl')
                        with open(out_file, 'a', encoding='utf-8') as fh:
                            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            
            # Predict on test set
            print(f"\nPredicting on test set...")
            for task in tasks:
                samples = test_records_by_task.get(task, [])
                if not samples:
                    print(f"  Skipping {task}: no test samples")
                    continue
                
                print(f"  Task: {task} ({len(samples)} samples)")
                
                for i in range(0, len(samples), batch_size):
                    batch_items = [samples[j].get('input') for j in range(i, min(i + batch_size, len(samples)))]
                    batch_enc = tokenizer(
                        batch_items,
                        return_tensors='pt',
                        max_length=512,
                        return_attention_mask=True,
                        padding=True,
                        truncation=True
                    )
                    batch_generation = predict_on_ids(
                        model,
                        tokenizer,
                        input_ids=batch_enc['input_ids'].to(device),
                        attention_mask=batch_enc['attention_mask'].to(device),
                        debug=debug
                    )
                    
                    for j, gen in enumerate(batch_generation):
                        src = samples[i + j].get('input')
                        ref = samples[i + j].get('output')
                        doc_id = samples[i + j].get('doc_id')
                        
                        rec = {
                            'epoch': epoch,
                            'dataset': ds_key,
                            'doc_id': doc_id,
                            'split': 'test',
                            'task': task,
                            'index': i + j,
                            'source': src,
                            'reference': ref,
                            'prediction': gen,
                        }
                        out_file = os.path.join(out_base, 'test.jsonl')
                        with open(out_file, 'a', encoding='utf-8') as fh:
                            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            
            print(f"Results saved to: {out_base}")


if __name__ == '__main__':
    # Example usage
    model_root = "/nfs/work/debi5729"
    split_group = "split1"
    #datasets = ["geneva"]  # Replace with actual dataset keys
    datasets = ["geneva", "wikievents", "casie", "genia2013", "m2e2", "rams"]
    amount = 1
    include_e2e = True
    tokenizer_model_dir = "google-t5/t5-base"
    #model_dir = f"{model_root}/google-t5-t5-large_split1_{'_'.join(datasets)}_amount_{amount}_e2e_True_full_latest_expressive_prompt"
    model_dir = f"{model_root}/google-t5-t5-base_active_learning_{'_'.join(datasets)}_amount_{amount}_1.0"
    # Predict on all tasks
    tasks = [
        'trigger_identification',
        'trigger_classification_pipeline',
        'trigger_classification_e2e',
        'argument_identification_e2e',
        'argument_extraction_pipeline',
        'event_extraction_e2e'
    ]
    
    main(datasets, epochs=[5, 10, 15, 20], tokenizer_model_dir=tokenizer_model_dir,  model_dir=model_dir, tasks=tasks, include_e2e=include_e2e, batch_size=16)
