import argparse
import copy
import json
import os
from typing import Dict, List, Tuple

from event_extraction_task_annotation_expressive_prompt import (
    create_argument_extraction_annotation,
    create_event_extraction_e2e_annotation,
    create_trigger_identification_annotation,
)
from new_event_types import (
    original_new_event_type_mappings,
    new_event_argument_roles_patterns,
    original_to_new_argument_role_lookup_by_dataset,
)


COMBINED_DATASETS = ("m2e2", "rams", "wikievents")
DEFAULT_SPLITS = {
    "train": "train.json",
    "val": "dev.json",
    "test": "test.json",
}


def build_event_type_lookup(
    mappings: Dict[str, List[List[str]]],
) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for dataset, pairs in mappings.items():
        dataset_lookup: Dict[str, str] = {}
        for pair in pairs:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue
            original_type, new_type = pair
            dataset_lookup[original_type] = new_type
        lookup[dataset] = dataset_lookup
    return lookup


def remap_event_types_in_item(
    data_point: Dict,
    ds_key: str,
    event_type_lookup: Dict[str, Dict[str, str]],
    keep_unmapped: bool = True,
) -> Tuple[Dict, int, int]:
    def return_new_argument_role(
        dataset_key: str,
        original_event_type: str,
        original_role: str,
    ) -> str:
        dataset_map = original_to_new_argument_role_lookup_by_dataset.get(dataset_key, {})
        event_map = dataset_map.get(original_event_type, {})
        if not event_map:
            return original_role

        if original_role in event_map:
            return event_map[original_role]

        # Be lenient with role casing differences across datasets.
        role_lower = str(original_role).lower()
        for role_key, mapped_role in event_map.items():
            if str(role_key).lower() == role_lower:
                return mapped_role

        return original_role

    remapped_item = copy.deepcopy(data_point)
    ds_lookup = event_type_lookup.get(ds_key, {})

    mapped_count = 0
    unmapped_count = 0

    for event_mention in remapped_item.get("event_mentions", []):
        original_type = event_mention.get("event_type")
        if not original_type:
            continue

        # Remap argument roles using the original dataset event type.
        args = event_mention.get("arguments")
        if args:
            for arg in args:
                role_field = None
                if arg.get("role") is not None:
                    role_field = "role"
                elif arg.get("role_type") is not None:
                    role_field = "role_type"
                elif arg.get("label") is not None:
                    role_field = "label"

                if role_field:
                    original_role = arg.get(role_field)
                    arg[role_field] = return_new_argument_role(
                        ds_key,
                        original_type,
                        original_role,
                    )

        new_type = ds_lookup.get(original_type)
        if new_type:
            event_mention["event_type"] = new_type
            mapped_count += 1
        else:
            unmapped_count += 1
            if not keep_unmapped:
                event_mention["event_type"] = "Unknown"

    return remapped_item, mapped_count, unmapped_count


def get_combined_dataset_instances(
    main_root: str,
    combined_ds_key: str ="news",
    datasets: Tuple[str, ...] = COMBINED_DATASETS,
    split_group: str = "split1",
    splits: Dict[str, str] = None,
    max_per_split: int = None,
    augment_word_generation: bool = False,
) -> Tuple[Dict, Dict]:
    if splits is None:
        splits = DEFAULT_SPLITS

    tasks = {
        "trigger_identification": {"train": [], "val": [], "test": []},
        "trigger_classification_pipeline": {"train": [], "val": [], "test": []},
        "trigger_classification_e2e": {"train": [], "val": [], "test": []},
        "argument_extraction_pipeline": {"train": [], "val": [], "test": []},
        "argument_identification_e2e": {"train": [], "val": [], "test": []},
        "trigger_identification_augument": {"train": [], "val": [], "test": []},
        "event_extraction_e2e": {"train": [], "val": [], "test": []},
    }

    stats = {
        "mapped": 0,
        "unmapped": 0,
        "items_processed": 0,
        "dataset_stats": {ds: {"mapped": 0, "unmapped": 0, "items": 0} for ds in datasets},
    }

    event_type_lookup = build_event_type_lookup(original_new_event_type_mappings)

    for ds_key in datasets:
        for split_name, split_file in splits.items():
            file_path = os.path.join(main_root, ds_key, split_group, split_file)
            if not os.path.exists(file_path):
                print(f"Warning: missing {file_path}, skipping")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                data = [json.loads(line) for line in f]

            if max_per_split is not None:
                data = data[:max_per_split]

            print(f"Loaded {len(data)} instances from {ds_key}/{split_group}/{split_file}")

            for i, item in enumerate(data):
                remapped_item, mapped_count, unmapped_count = remap_event_types_in_item(
                    item,
                    ds_key,
                    event_type_lookup,
                    keep_unmapped=True,
                )

                stats["mapped"] += mapped_count
                stats["unmapped"] += unmapped_count
                stats["items_processed"] += 1
                stats["dataset_stats"][ds_key]["mapped"] += mapped_count
                stats["dataset_stats"][ds_key]["unmapped"] += unmapped_count
                stats["dataset_stats"][ds_key]["items"] += 1

                doc_id = f"{ds_key}_{split_name}_{i}"

                trig_ann = create_trigger_identification_annotation(
                    remapped_item,
                    ds_key=combined_ds_key,
                    augument_word_generation=augment_word_generation,
                )
                if trig_ann:
                    ident = trig_ann.get("identification")
                    clas_pipeline = trig_ann.get("classification_pipeline")
                    clas_e2e = trig_ann.get("classification_e2e")
                    ident_aug = trig_ann.get("identification_augument")

                    if ident_aug:
                        tasks["trigger_identification_augument"][split_name].append(
                            {
                                "doc_id": doc_id,
                                "source_dataset": ds_key,
                                "input": ident_aug["input"],
                                "output": ident_aug["output"],
                            }
                        )
                    if ident:
                        tasks["trigger_identification"][split_name].append(
                            {
                                "doc_id": doc_id,
                                "source_dataset": ds_key,
                                "input": ident["input"],
                                "output": ident["output"],
                            }
                        )
                    if clas_pipeline:
                        tasks["trigger_classification_pipeline"][split_name].append(
                            {
                                "doc_id": doc_id,
                                "source_dataset": ds_key,
                                "input": clas_pipeline["input"],
                                "output": clas_pipeline["output"],
                            }
                        )
                    if clas_e2e:
                        tasks["trigger_classification_e2e"][split_name].append(
                            {
                                "doc_id": doc_id,
                                "source_dataset": ds_key,
                                "input": clas_e2e["input"],
                                "output": clas_e2e["output"],
                            }
                        )

                argument_identification, argument_extraction_list = create_argument_extraction_annotation(
                    doc_id,
                    remapped_item,
                    ds_key=combined_ds_key,
                )
                if argument_extraction_list:
                    for record in argument_extraction_list:
                        record["source_dataset"] = ds_key
                    tasks["argument_extraction_pipeline"][split_name].extend(argument_extraction_list)
                if argument_identification:
                    argument_identification["source_dataset"] = ds_key
                    tasks["argument_identification_e2e"][split_name].append(argument_identification)

                e2e_ann = create_event_extraction_e2e_annotation(remapped_item, ds_key=combined_ds_key)
                if e2e_ann:
                    tasks["event_extraction_e2e"][split_name].append(
                        {
                            "doc_id": doc_id,
                            "source_dataset": ds_key,
                            "input": e2e_ann["input"],
                            "output": e2e_ann["output"],
                        }
                    )

    return tasks, stats


def save_tasks_to_jsonl(tasks: Dict, output_root: str) -> None:
    os.makedirs(output_root, exist_ok=True)

    for task_name, split_dict in tasks.items():
        task_dir = os.path.join(output_root, task_name)
        os.makedirs(task_dir, exist_ok=True)

        for split_name, records in split_dict.items():
            out_file = os.path.join(task_dir, f"{split_name}.jsonl")
            with open(out_file, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"Saved {len(records)} records -> {out_file}")


def main() -> None:
    MAIN_ROOT = "/fs/s6k/groups/agaai/processed_data"
    OUTPUT_ROOT = "./combined_tasks"
  
    SPLITS = {
    "train": "train.json",
    "val": "dev.json",
    "test": "test.json"
     }
    parser = argparse.ArgumentParser(
        description=(
            "Create combined training data from m2e2/rams/wikievents using "
            "generalized event types from original_new_event_type_mappings."
        )
    )
    
    parser.add_argument("--split-group", type=str, default="split1", help="Split group folder name")
    parser.add_argument("--max-per-split", type=int, default=100, help="Optional max number of instances per split")
    parser.add_argument(
        "--no-augment-trigger-words",
        action="store_true",
        help="Disable trigger identification augmentation examples",
    )

    args = parser.parse_args()

    tasks, stats = get_combined_dataset_instances(
        main_root=MAIN_ROOT,
        split_group=args.split_group,
        splits=SPLITS,
        max_per_split=args.max_per_split,
        augment_word_generation=not args.no_augment_trigger_words,
    )

    save_tasks_to_jsonl(tasks, OUTPUT_ROOT)

    print("\nEvent-type remapping summary")
    print(f"Items processed: {stats['items_processed']}")
    print(f"Mapped event mentions: {stats['mapped']}")
    print(f"Unmapped event mentions: {stats['unmapped']}")
    for ds_key, ds_stats in stats["dataset_stats"].items():
        print(
            f"  {ds_key}: items={ds_stats['items']}, "
            f"mapped={ds_stats['mapped']}, unmapped={ds_stats['unmapped']}"
        )


if __name__ == "__main__":
    main()
