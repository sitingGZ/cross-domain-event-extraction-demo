import torch

from event_extraction_task_annotation_with_index import get_dataset_instances
from event_extraction_task_annotation_without_index import get_dataset_instances_no_index, get_dataset_instances_no_index_e2e, get_dataset_instances_no_index_all
from event_extraction_task_annotation_expressive_prompt import get_dataset_instances_no_index_all as get_dataset_instances_no_index_all_expressive_prompt


class TokenizedEventDataset(torch.utils.data.Dataset):
    """Wraps a list of {'input','output',...} records and tokenizes on initialization.
    The dataset returns dicts with keys expected by HF Trainer when using a data collator:
    - 'input_ids', 'attention_mask', 'labels' (lists of ints)
    """
    def __init__(self, records, tokenizer):
        self.tokenizer = tokenizer
        # Set reasonable max lengths to avoid overflow; BART's model_max_length can be huge
        self.max_input_length = min(512, tokenizer.model_max_length) if hasattr(tokenizer, 'model_max_length') else 512
        self.max_output_length = min(512, tokenizer.model_max_length) if hasattr(tokenizer, 'model_max_length') else 512
        self.examples = []
        if not records:
            return
        for r in records:
            src = r.get('input')
            tgt = r.get('output')
            if src is None or tgt is None:
                continue
            # encode inputs and targets but do not pad here (collator will pad)
            try:
                enc = tokenizer(src, truncation=True, max_length=self.max_input_length, return_attention_mask=True)
                with tokenizer.as_target_tokenizer():
                    lab = tokenizer(tgt, truncation=True, max_length=self.max_output_length)
                # store raw ids; collator will pad to batch
                self.examples.append({
                    'input_ids': enc['input_ids'],
                    'attention_mask': enc['attention_mask'],
                    'labels': lab['input_ids']
                })
            except Exception as e:
                # Skip records that cause tokenization errors
                print(f"Warning: skipping record due to tokenization error: {e}")
                continue

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

tasks = {
    'trigger_identification': {'train': [], 'val': [], 'test': []},
    'trigger_classification': {'train': [], 'val': [], 'test': []},
    'argument_extraction': {'train': [], 'val': [], 'test': []},
    'argument_identification': {'train': [], 'val': [], 'test': []},
  }


class TriggerEventTokenIdentificationDataset(torch.utils.data.Dataset):
    """Wraps a list of {'input', 'attention_mask','labels', 'token_labels'} for trigger identification task
       for other tasks wraps a list of {'input', 'attention_mask','labels'}
       givent the records and tokenizes on initialization.
    """
    def __init__(self, records, tokenizer):
        self.tokenizer = tokenizer
        # Set reasonable max lengths to avoid overflow; BART's model_max_length can be huge
        self.max_input_length = min(512, tokenizer.model_max_length) if hasattr(tokenizer, 'model_max_length') else 512
        self.max_output_length = min(512, tokenizer.model_max_length) if hasattr(tokenizer, 'model_max_length') else 512
        self.examples = []
        self.label_map = {"b-trigger": 1, "i-trigger": 2, "o-trigger": 0}
        if not records:
            return
        for r in records:
            current_example = {}
            src = r.get('input')
            tgt = r.get('output')
            token_tgt = r.get('token_labels', None)
            if src is None or tgt is None:
                continue
            # encode inputs and targets but do not pad here (collator will pad)
            try:
                enc = tokenizer(src, truncation=True, max_length=self.max_input_length, return_attention_mask=True)
                with tokenizer.as_target_tokenizer():
                    lab = tokenizer(tgt, truncation=True, max_length=self.max_output_length)
                # store raw ids; collator will pad to batch
                current_example['input_ids'] = enc['input_ids']
                current_example['attention_mask'] = enc['attention_mask']
                current_example['labels'] = lab['input_ids']
               
            except Exception as e:
                # Skip records that cause tokenization errors
                print(f"Warning: skipping record due to tokenization error: {e}")
                continue
            if token_tgt is not None:
                current_example['token_labels'] = [self.label_map[l] for l in token_tgt]
                current_example['token_input_ids'] = r.get('token_input_ids', [])
                current_example['token_attention_mask'] = r.get('token_attention_mask', [])
            else:
                current_example['token_labels'] = []
                current_example['token_input_ids'] = []
                current_example['token_attention_mask'] = []
            self.examples.append(current_example) 

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx] 
    
def load_split_datasets_with_token_labels_for_trigger_identification(main_root, ds_keys, split_group, tokenizer, tasks = ['trigger_identification', 'trigger_classification', 'argument_identification', 'argument_extraction'], with_trigger_index=True, splits=None, amount=None):
    train_records = []
    val_records = []
    
    train_token_labels = []
    val_token_labels = []
        
    for ds_key in ds_keys:
        
        instances = get_dataset_instances_and_token_labels_no_index(main_root, ds_key, tokenizer, split_group=split_group, splits=splits)
        for task_name in tasks:
            split_dict = instances.get(task_name, {})
            train_records.extend(split_dict.get('train', []))
            val_records.extend(split_dict.get('val', []))
            
            # Take only percentage of instances instead of full dataset
            if amount is not None:
                train_records.extend(split_dict.get('train', [])[:int(len(split_dict.get('train', [])) * amount)])
                val_records.extend(split_dict.get('val', [])[:int(len(split_dict.get('val', [])) * amount)])
    
    train_ds = TriggerEventTokenIdentificationDataset(train_records, tokenizer)
    val_ds = TriggerEventTokenIdentificationDataset(val_records, tokenizer) 
            
    return train_ds, val_ds

def load_split_datasets(main_root, ds_keys, split_group, tokenizer, tasks = ['trigger_identification', 'trigger_classification', 'argument_identification', 'argument_extraction'], with_trigger_index=True, splits=None, amount=None):
    
    train_records = []
    val_records = []
    for ds_key in ds_keys:
        if with_trigger_index:
            instances = get_dataset_instances(main_root, ds_key, split_group=split_group, splits=splits)
        else:
            instances = get_dataset_instances_no_index(main_root, ds_key, split_group=split_group, splits=splits)
        for task_name in tasks:
            split_dict = instances.get(task_name, {})
            train_records.extend(split_dict.get('train', []))
            val_records.extend(split_dict.get('val', []))
            
            # Take only percentage of instances instead of full dataset
            if amount is not None:
                train_records.extend(split_dict.get('train', [])[:int(len(split_dict.get('train', [])) * amount)])
                val_records.extend(split_dict.get('val', [])[:int(len(split_dict.get('val', [])) * amount)])
            
    train_ds = TokenizedEventDataset(train_records, tokenizer)
    val_ds = TokenizedEventDataset(val_records, tokenizer)
    return train_ds, val_ds

def load_e2e_datasets(main_root, ds_keys, split_group, tokenizer, tasks = ['event_extraction_e2e'],  splits=None, amount=None):
    
    train_records = []
    val_records = []
    for ds_key in ds_keys:
        instances = get_dataset_instances_no_index_e2e(main_root, ds_key, split_group=split_group, splits=splits)
        for task_name in tasks:
            split_dict = instances.get(task_name, {})
            train_records.extend(split_dict.get('train', []))
            val_records.extend(split_dict.get('val', []))
            
            # Take only percentage of instances instead of full dataset
            if amount is not None:
                train_records.extend(split_dict.get('train', [])[:int(len(split_dict.get('train', [])) * amount)])
                val_records.extend(split_dict.get('val', [])[:int(len(split_dict.get('val', [])) * amount)])
            
    train_ds = TokenizedEventDataset(train_records, tokenizer)
    val_ds = TokenizedEventDataset(val_records, tokenizer)
    return train_ds, val_ds

def load_datasets_all(main_root, ds_keys, split_group, tokenizer, tasks,  use_expressive_prompt=False, splits=None, amount=None):
    
    train_records = []
    val_records = []
    for ds_key in ds_keys:
        if use_expressive_prompt:
            instances = get_dataset_instances_no_index_all_expressive_prompt(main_root, ds_key, split_group=split_group, splits=splits)
        else:
            instances = get_dataset_instances_no_index_all(main_root, ds_key, split_group=split_group, splits=splits)
        #for task_name, split_dict in instances.items():
        #    train_records.extend(split_dict.get('train', []))
        #    val_records.extend(split_dict.get('val', []))
        for task_name in tasks:
            split_dict = instances.get(task_name, {})
            train_records.extend(split_dict.get('train', []))
            val_records.extend(split_dict.get('val', []))
            # Take only percentage of instances instead of full dataset
            if amount is not None:
                train_records.extend(split_dict.get('train', [])[:int(len(split_dict.get('train', [])) * amount)])
                val_records.extend(split_dict.get('val', [])[:int(len(split_dict.get('val', [])) * amount)])
            
    train_ds = TokenizedEventDataset(train_records, tokenizer)
    val_ds = TokenizedEventDataset(val_records, tokenizer)
    return train_ds, val_ds



if __name__ == "__main__":
    # Example usage
    from transformers import AutoTokenizer

    main_root = "/nfs/data/debi5729/processed_data"
    split_group = "split1"
    datasets = ['geneva']
    tokenizer = AutoTokenizer.from_pretrained("google-t5/t5-small")
    tasks = ['trigger_identification', 'trigger_classification', 'argument_identification', 'argument_extraction']
    # check on sample from train by each task
    instances = get_dataset_instances_no_index(main_root, datasets[0], split_group=split_group, splits=None)
    for task_name in tasks:
            split_dict = instances.get(task_name, {})
            train_records = split_dict.get('train', [])
            print(task_name)
            print(train_records[0])
    # check e2e
    instances = get_dataset_instances_no_index_e2e(main_root, datasets[0], split_group=split_group, splits=None)
    split_dict = instances.get('event_extraction_e2e', {})
    train_records = split_dict.get('train', [])
    print('event_extraction_e2e')
    print(train_records[0])
    
    
   
