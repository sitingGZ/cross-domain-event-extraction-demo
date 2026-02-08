
import argparse
from transformers import AutoTokenizer, T5ForConditionalGeneration, TrainingArguments, Trainer, DataCollatorForSeq2Seq, TrainerCallback
from dataloader import load_split_datasets, load_e2e_datasets, load_datasets_all, TokenizedEventDataset
import torch
import os


class SaveEveryNEpochsCallback(TrainerCallback):
        def __init__(self, save_every_n_epochs, output_dir):
            self.n = save_every_n_epochs
            self.output_dir = output_dir
            self.last_good_epoch = 0

        def on_epoch_end(self, args, state, control, **kwargs):
            # state.epoch may be fractional; convert to int when available
            try:
                epoch = int(state.epoch) if state.epoch is not None else None
            except Exception:
                epoch = None
            
            # Check for NaN in recent log history
            has_nan = False
            if hasattr(state, 'log_history') and len(state.log_history) > 0:
                recent_logs = state.log_history[-5:]  # Check last 5 log entries
                for log_entry in recent_logs:
                    grad_norm = log_entry.get('grad_norm')
                    if grad_norm is not None and (grad_norm != grad_norm or str(grad_norm) == 'nan'):
                        has_nan = True
                        break
            
            if epoch and epoch % self.n == 0:
                if has_nan:
                    print(f"WARNING: Skipping checkpoint save at epoch {epoch} due to NaN grad_norm. Using last good checkpoint at epoch {self.last_good_epoch}.")
                    return
                self.last_good_epoch = epoch
                ckpt_dir = os.path.join(self.output_dir, f"checkpoint-epoch-{epoch}")
                os.makedirs(ckpt_dir, exist_ok=True)
                model = kwargs.get('model')
                tokenizer = kwargs.get('tokenizer')
                if model is not None:
                    try:
                        model.save_pretrained(ckpt_dir)
                        print(f"Saved model to {ckpt_dir}")
                    except Exception as e:
                        print(f"ERROR saving model: {e}")
                if tokenizer is not None:
                    try:
                        tokenizer.save_pretrained(ckpt_dir)
                        print(f"Saved tokenizer to {ckpt_dir}")
                    except Exception as e:
                        print(f"ERROR saving tokenizer: {e}")
                # Save trainer state JSON
                state_file = os.path.join(ckpt_dir, 'trainer_state.json')
                try:
                    import json
                    # Try different serialization methods depending on transformers version
                    if hasattr(state, 'to_json_string'):
                        state_json = state.to_json_string()
                    else:
                        # Fall back to manual serialization
                        state_dict = state.__dict__ if hasattr(state, '__dict__') else vars(state)
                        state_json = json.dumps(state_dict, indent=2, default=str)
                    
                    if not state_json or state_json.strip() == "":
                        print(f"WARNING: trainer state JSON is empty at epoch {epoch}")
                    with open(state_file, 'w') as hf:
                        hf.write(state_json)
                        hf.flush()
                        os.fsync(hf.fileno())
                    print(f"Saved trainer state to {state_file}")
                except Exception as e:
                    print(f"ERROR saving trainer state: {e}")

def get_train_val_datasets(datasets, split_group, tokenizer, tasks, with_trigger_index=True, amount=None, e2e=False):
    main_root = "/nfs/data/debi5729/processed_data"
        
    train_ds, val_ds = load_split_datasets(main_root, datasets, split_group, tokenizer, tasks = tasks, with_trigger_index=with_trigger_index, amount=amount)
    if e2e:
        train_ds_e2e, val_ds_e2e = load_e2e_datasets(main_root, datasets, split_group, tokenizer, tasks = ['event_extraction_e2e'], amount=amount)
        train_ds.extend(train_ds_e2e)
        val_ds.extend(val_ds_e2e)
    return train_ds, val_ds

def get_all_train_val_datasets(datasets, split_group, tokenizer, tasks, use_expressive_prompt=True, amount=None):
    main_root = "/nfs/data/debi5729/processed_data"
    train_ds, val_ds = load_datasets_all(main_root, datasets, split_group, tokenizer, use_expressive_prompt=use_expressive_prompt, tasks=tasks, splits=None, amount=amount)
    return train_ds, val_ds

def train_dataset(train_ds, val_ds,epochs = 41, save_every_n_epochs=5, model_name="google-t5/t5-small", per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=0.1, e2e=True):
    
    main_root = "/nfs/data/debi5729/processed_data"
    split_group = "split1"
    output_dir = "/nfs/work/debi5729/"
    # Lower learning rate for larger models to prevent instability
  
    if 'base' in model_name or 'small' in model_name:
        learning_rate = 5e-05
    else:
        learning_rate = 1e-05
        # Keep large-model batches modest unless explicitly lowered by caller
        #per_device_train_batch_size = min(per_device_train_batch_size, 8)
        #per_device_eval_batch_size = min(per_device_eval_batch_size, 8)
        
    seed = 42
    print(f"Training with model: {model_name}, batch size: {per_device_train_batch_size}, amount: {amount}, e2e: {e2e}")
    
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    # Reduce activation memory
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
    if hasattr(model, "config"):
        model.config.use_cache = False
    print(f"Loaded model and tokenizer for {model_name}")
    # move model to GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    print(f"Using device: {device}")
    
    #datasets = ["geneva", 'wikievents', 'casie', 'genia2013', 'm2e2', 'rams' ]  # Replace with actual dataset keys
    #datasets = ['rams']
    #datasets = ['wikievents', 'casie', 'genia2013', 'm2e2', 'rams' ]
    #datasets = ['wikievents', 'rams' ]
    
    with_trigger_index = False
    #with_trigger_index = True
    output_dir += f"{model_name.replace('/', '-')}_{split_group}_{'_'.join(datasets)}_amount_{amount}_e2e_{e2e}"
    print(f"Output directory: {output_dir}")
    

    

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=tokenizer.pad_token_id)

    # Build TrainingArguments with only supported kwargs to maintain compatibility
    import inspect
    ta_sig = inspect.signature(TrainingArguments)
    ta_params = ta_sig.parameters
    print('training parameters:', ta_params.keys())

    kwargs = {}
    def _add(k, v):
        if k in ta_params:
            kwargs[k] = v
            
        else:
            print(f"Warning: TrainingArguments has no parameter named '{k}'; skipping.")


    
    _add('output_dir', output_dir)
    _add('num_train_epochs', epochs)
    _add('per_device_train_batch_size', per_device_train_batch_size)
    _add('per_device_eval_batch_size', per_device_eval_batch_size)
    _add('per_gpu_train_batch_size', per_device_train_batch_size)
    _add('per_gpu_eval_batch_size', per_device_eval_batch_size)
    # evaluation strategy (may not exist in older transformers)
    if len(val_ds) > 0:
        _add('evaluation_strategy', 'steps')
        _add('eval_steps', 500)
    else:
        _add('evaluation_strategy', 'no')
    _add('save_steps', 500)
    _add('logging_steps', 100)
    _add('learning_rate', learning_rate)
    _add('save_total_limit', 2)
    _add('seed', seed)
    _add('max_grad_norm', 1.0)
    _add('warmup_ratio', 0.1)
    _add('remove_unused_columns', False)
    _add('predict_with_generate', True)
    _add('gradient_accumulation_steps', 4)
    _add('gradient_checkpointing', True)
    # Enable efficient multi-GPU training with DDP
    if torch.cuda.device_count() > 1:
        _add('ddp_find_unused_parameters', False)
        
    # Precision & stability: avoid fp16 if it causes NaNs; prefer bf16 on modern GPUs
    _add('fp16', False)
    _add('bf16', torch.cuda.is_available())
    # disable built-in saving; we'll use callback-based epoch saves if supported
    _add('save_strategy', 'no')

    training_args = TrainingArguments(**kwargs)

    # Callback to save every N epochs
    
    save_callback = SaveEveryNEpochsCallback(save_every_n_epochs, output_dir)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds if len(train_ds) > 0 else None,
        eval_dataset=val_ds if len(val_ds) > 0 else None,
        data_collator=data_collator,
        tokenizer=tokenizer,
        callbacks=[save_callback],
    )

    if len(train_ds) == 0:
        print("No training examples found — aborting.")
        return

    trainer.train()
    trainer.save_model(output_dir)


def continue_train_dataset(train_ds, val_ds, checkpoint_dir, tokenizer_dir=None, extra_epochs=10, save_every_n_epochs=5, per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=0.1, e2e=True):
    """Continue training from an existing checkpoint, preserving trainer state.

    - tokenizer_dir: optional path to load tokenizer when checkpoint lacks tokenizer files.
    - extra_epochs: number of additional epochs to train; total epochs = last_epoch + extra_epochs.
    """
    output_dir = f"{checkpoint_dir}_continued"

    trainer_state_path = os.path.join(checkpoint_dir, "trainer_state.json")
    last_epoch = 0.0
    last_lr = None
    if os.path.exists(trainer_state_path):
        try:
            import json
            with open(trainer_state_path, "r") as sf:
                content = sf.read().strip()
            if not content:
                print(f"Warning: trainer_state.json is empty; using default initial state.")
            else:
                state = json.loads(content)
                if isinstance(state, dict):
                    if state.get('epoch') is not None:
                        try:
                            last_epoch = float(state['epoch'])
                        except Exception:
                            last_epoch = 0.0
                    if isinstance(state.get('log_history'), list):
                        for entry in reversed(state['log_history']):
                            lr_val = entry.get('learning_rate') if isinstance(entry, dict) else None
                            if lr_val is not None:
                                try:
                                    last_lr = float(lr_val)
                                    break
                                except Exception:
                                    last_lr = None
        except Exception as exc:
            print(f"Warning: failed to read trainer_state.json: {exc}; using default initial state.")

    try:
        model_name = T5ForConditionalGeneration.from_pretrained(checkpoint_dir).config.name_or_path
    except Exception:
        model_name = checkpoint_dir

    if last_lr is not None:
        learning_rate = last_lr
    else:
        if 'base' in model_name or 'small' in model_name:
            learning_rate = 5e-05
        else:
            learning_rate = 1e-05
            #per_device_train_batch_size = min(per_device_train_batch_size, 8)
            #per_device_eval_batch_size = min(per_device_eval_batch_size, 8)

    target_total_epochs = last_epoch + extra_epochs

    seed = 42
    print(f"Continuing training from checkpoint: {checkpoint_dir}\nModel: {model_name}, batch size: {per_device_train_batch_size}, amount: {amount}, e2e: {e2e}")
    print(f"Last epoch: {last_epoch:.2f} -> Target total epochs: {target_total_epochs:.2f}")
    print(f"Learning rate (resumed): {learning_rate}")

    tokenizer_path = tokenizer_dir if tokenizer_dir else checkpoint_dir
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    model = T5ForConditionalGeneration.from_pretrained(checkpoint_dir)

    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
    if hasattr(model, "config"):
        model.config.use_cache = False

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    print(f"Using device: {device}")

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=tokenizer.pad_token_id)

    import inspect
    ta_sig = inspect.signature(TrainingArguments)
    ta_params = ta_sig.parameters

    kwargs = {}

    def _add(k, v):
        if k in ta_params:
            kwargs[k] = v
        else:
            print(f"Warning: TrainingArguments has no parameter named '{k}'; skipping.")

    _add('output_dir', output_dir)
    _add('num_train_epochs', target_total_epochs)
    _add('per_device_train_batch_size', per_device_train_batch_size)
    _add('per_device_eval_batch_size', per_device_eval_batch_size)
    _add('per_gpu_train_batch_size', per_device_train_batch_size)
    _add('per_gpu_eval_batch_size', per_device_eval_batch_size)
    if len(val_ds) > 0:
        _add('evaluation_strategy', 'steps')
        _add('eval_steps', 500)
    else:
        _add('evaluation_strategy', 'no')
    _add('save_steps', 500)
    _add('logging_steps', 100)
    _add('learning_rate', learning_rate)
    _add('save_total_limit', 2)
    _add('seed', seed)
    _add('max_grad_norm', 1.0)
    _add('warmup_ratio', 0.1)
    _add('remove_unused_columns', False)
    _add('predict_with_generate', True)
    _add('gradient_accumulation_steps', 4)
    _add('gradient_checkpointing', True)
    if torch.cuda.device_count() > 1:
        _add('ddp_find_unused_parameters', False)
    _add('fp16', False)
    _add('bf16', torch.cuda.is_available())
    _add('save_strategy', 'no')

    training_args = TrainingArguments(**kwargs)

    save_callback = SaveEveryNEpochsCallback(save_every_n_epochs, output_dir)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds if len(train_ds) > 0 else None,
        eval_dataset=val_ds if len(val_ds) > 0 else None,
        data_collator=data_collator,
        tokenizer=tokenizer,
        callbacks=[save_callback],
    )

    if len(train_ds) == 0:
        print("No training examples found — aborting.")
        return

    trainer.train(resume_from_checkpoint=checkpoint_dir)
    trainer.save_model(output_dir)


if __name__ == '__main__':
    #train_dataset(datasets = ['geneva'], epochs = 41, model_name="google-t5/t5-3b")
    datasets = ['geneva','wikievents', 'casie', 'genia2013', 'm2e2', 'rams' ]
    #datasets = ['geneva' ]
    tasks = {
        'trigger_identification': {'train': [], 'val': [], 'test': []},
        'trigger_classification_pipeline': {'train': [], 'val': [], 'test': []},
        'trigger_classification_e2e': {'train': [], 'val': [], 'test': []},
        'argument_extraction_pipeline': {'train': [], 'val': [], 'test': []},
        'argument_identification_e2e': {'train': [], 'val': [], 'test': []},
        'event_extraction_e2e': {'train': [], 'val': [], 'test': []}
    }
    tasks = list(tasks.keys())
    #datasets = ['genia2013']
    #datasets = ['rams']
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-large", per_device_train_batch_size=32, per_device_eval_batch_size=16, amount=0.1)
    
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-base", per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=0.25)
    #datasets = ['wikievents', 'rams']
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-base", per_device_train_batch_size=40, per_device_eval_batch_size=32, amount=1)
    
    #datasets = ['casie']
    #e2e = True
    
    #train_ds, val_ds = get_train_val_datasets(datasets, split_group="split1", tokenizer=AutoTokenizer.from_pretrained("google-t5/t5-base"), amount=1, e2e=e2e)
    #train_dataset(train_ds, val_ds, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-base", per_device_train_batch_size=40, per_device_eval_batch_size=32, amount=1, e2e=e2e)
    model_name="google-t5/t5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    #datasets = ['genia2013']
    e2e = "True_full_latest_expressive_prompt"
    amount = 1
    #tasks = ['trigger_identification', 'trigger_classification',  'argument_identification', 'argument_extraction', 'event_extraction_e2e']
    #train_ds, val_ds = get_train_val_datasets(datasets, split_group="split1", tokenizer=AutoTokenizer.from_pretrained("google-t5/t5-base"), amount=1, e2e=e2e)
    train_ds, val_ds = get_all_train_val_datasets(datasets, split_group="split1", tokenizer=tokenizer, tasks=tasks, amount=amount)
    train_dataset(train_ds, val_ds, epochs = 10, save_every_n_epochs=5, model_name=model_name, per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=amount, e2e=e2e)
    #checkpoint_dir = f"/nfs/work/debi5729/{model_name.replace('/', '-')}_split1_{'_'.join(datasets)}_amount_{amount}_e2e_{e2e}/checkpoint-epoch-30"
    #continue_train_dataset(train_ds, val_ds, checkpoint_dir, tokenizer_dir=model_name, extra_epochs=10, save_every_n_epochs=10, per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=amount, e2e=e2e)
    
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-large", per_device_train_batch_size=64, per_device_eval_batch_size=32, amount=1.0)
    
    
    #datasets = ['rams']
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-large", per_device_batch_size=16, amount=1)
    
    #datasets = ['m2e2']
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-large", per_device_batch_size=16, amount=1)
    
    #datasets = ['casie']
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-large", per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=1)
    
    #datasets = ['genia2013']
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-large", per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=1) 
    
    #datasets = ['wikievents']
    #train_dataset(datasets = datasets, epochs = 41, save_every_n_epochs=10, model_name="google-t5/t5-large", per_device_train_batch_size=32, per_device_eval_batch_size=32, amount=1) 
    
    #train_dataset(datasets = ['casie'], epochs = 41, model_name="google-t5/t5-small")
    #train_dataset(datasets = ['genia2013'], epochs = 41, model_name="google-t5/t5-small")
    #train_dataset(datasets = ['m2e2'], epochs = 41, model_name="google-t5/t5-small")
    #train_dataset(datasets = ['rams'], epochs = 41, model_name="google-t5/t5-small")
    #
