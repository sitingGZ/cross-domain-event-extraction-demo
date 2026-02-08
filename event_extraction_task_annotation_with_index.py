# imports used by the annotation helpers
import re
from pattern_tagprime import event_type_tags,patterns, role_type_tags
import json
import os
from transformers import T5Tokenizer

TRIGGER_TASKS = {
     "TI": "Trigger Identification",
     "TC": "Trigger Classification"
}
ARGUMENT_TASKS = {
     "AI": "Argument Identification",
     "AE": "Argument Extraction",
 }
 
#domain = "geneva"  # change as needed
#TEMPLATE_ONE_input = f"domain: {domain}. trigger>: The bomb exploded and the victim was injured." 
#TEMPLATE_ONE_output = "The bomb trigger>exploded<extra_id_0> and the victim was injured." 

#TEMPLATE_TWO_input = f"domain: {domain}. trigger types: The bomb trigger>exploded<extra_id_0> and the victim was injured."
#TEMPLATE_TWO_output = "<extra_id_0> exploded=attack explosion "

#TEMPLATE_THREE_input = f"domain: {domain}. extract arguments Agent | Victim for event Attack explosion: The bomb trigger>exploded<extra_id_0> and the victim was injured."
#TEMPLATE_THREE_output = "<extra_id_0> The bomb=Agent | victim=Victim"
def get_json_data(main_path="processed_data/m2e2", split_group="split1", split="train.json"):
    file_path = os.path.join(main_path,split_group, split)
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]
    


def create_trigger_identification_annotation(data_point, ds_key="geneva", use_human_readable=False, t5_tokenizer=None):
  """
  Produce T5-style sentinel templates for trigger identification and
  classification.

  Returns a dict with keys:
    - 'template_one_input': input with trigger spans replaced by sentinels
    - 'template_one_output': label sequence mapping sentinels to span texts
    - 'token_level_labels': a list of 0/1 labels per token for trigger identification
    - 'template_two_input': same as template_one_input (for classification)
    - 'template_two_output': label sequence mapping sentinels to span=class
 The labels are constructed as
  `trigger {idx}> span_text > ` where
  N = number of spans. For classification, span_text_i is replaced by
  `span_text_i=HumanReadableClass`.
  """

  tokens = data_point.get("tokens")
  event_mentions = data_point.get("event_mentions", [])

  if not tokens:
    raise ValueError("data_point must contain 'tokens' list")

  # collect unique trigger spans sorted left-to-right
  spans = []
  seen = set()
  for ev in event_mentions:
    trig = ev.get("trigger")
    if not trig:
      continue
    try:
      s = int(trig.get("start"))
      e = int(trig.get("end"))
    except Exception:
      continue
    if s < 0 or e <= s or s >= len(tokens):
      continue
    e = min(e, len(tokens))
    if (s, e) not in seen:
      spans.append((s, e))
      seen.add((s, e))

  spans = sorted(spans)

  # helper to clean spacing/punctuation
  def _clean_space_punct(t: str) -> str:
    t = re.sub(r"\s+([,\.\?\!;:%])", r"\1", t)
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"\s+\)", ")", t)
    t = re.sub(r"\s+\"", '"', t)
    t = re.sub(r'\"\s+', '"', t)
    return re.sub(r"\s+", " ", t).strip()


  # build classification label: trigger> span0=Class | trigger> span1=Class | ... trigger> spanN=Class
  class_labels = []
  for idx, (s, e) in enumerate(spans):
    span_text = _clean_space_punct(" ".join(tokens[s:e]))
    # find associated event type(s)
    event_types = [ev.get("event_type") for ev in event_mentions if ev.get("trigger") and int(ev.get("trigger").get("start")) == s and int(ev.get("trigger").get("end")) == e]
    #print(f"Span '{span_text}' at ({s},{e}) has event types: {event_types}")
    primary = event_types[0] if event_types else None
    human_name = None
    # prefer dataset passed in, otherwise fallback to module-level domain 
    if primary:
      # try exact lookup on the chosen dataset
      human_name = event_type_tags.get(ds_key, {}).get(primary)
      # try common casings / variants if not found
      if human_name is None:
        domain_map = event_type_tags.get(ds_key, {})
        human_name = domain_map.get(primary.lower()) or domain_map.get(primary.upper())
      if human_name is None:
        alt = primary.replace(':', '_').replace('/', '_').replace('-', '_')
        human_name = event_type_tags.get(ds_key, {}).get(alt)
      # last resort: search all domains for the key
      if human_name is None:
        for dname, dm in event_type_tags.items():
          if primary in dm:
            human_name = dm.get(primary)
            break
      if human_name is None:
        print(f"Warning: no human-readable mapping for event_type '{primary}' in dataset '{ds_key}'")
    if not human_name:
      human_name = primary if primary else "Unknown"
    #class_labels.append(f"<extra_id_{idx}> {span_text}={human_name}")
    if use_human_readable:
      class_labels.append(f"trigger {idx+1}> {span_text}>={human_name}")
    else:
      class_labels.append(f"trigger {idx+1}> {span_text}>={primary if primary else 'Unknown'}")
  #class_labels.append(f"<extra_id_{len(spans)}>")
  template_two_output = " | ".join(class_labels)

  # Build tagged sentence using 'trigger>' as opening tag and
  # '<extra_id_{i}>' as the closing marker after the span, as requested.
  tagged_parts = []
  cursor = 0
  for idx, (s, e) in enumerate(spans):
    if cursor < s:
      tagged_parts.extend(tokens[cursor:s])
    # opening marker is 'trigger>' (no leading <), then span text, then closing sentinel
    span_text_tokens = tokens[s:e]
    span_text = _clean_space_punct(" ".join(span_text_tokens))
    tagged_parts.append(f"trigger {idx+1}> {span_text}>")
    cursor = e
  if cursor < len(tokens):
    tagged_parts.extend(tokens[cursor:])

  tagged_sentence = _clean_space_punct(" ".join(tagged_parts))
  plain_text = _clean_space_punct(" ".join(tokens))
  template_one_input = f"domain: {ds_key}. trigger>: {plain_text}"
  template_one_output = tagged_sentence
  template_two_input = f"domain: {ds_key}. trigger>=type: {tagged_sentence}"

  # handle no-spans case: create a canonical NO_TRIGGER label if desired
  if not spans:
    #template_one_output = "<extra_id_0> NO_TRIGGER <extra_id_1>"
    #template_two_output = "<extra_id_0> NO_TRIGGER <extra_id_1>"
    return None
  
  else:
    return {
    'identification': {'input': template_one_input, 'output': template_one_output},
    'classification': {'input': template_two_input, 'output': template_two_output},
   }




def create_argument_extraction_annotation(data_point, ds_key="geneva", use_human_readable=False):
  """
  Extract argument-identification and argument-extraction pairs for a data point.

  Returns (argument_identification_dict or None, extraction_records list or None).
  Each extraction record is a dict with keys: 'event_id', 'extraction_input', 'extraction_output'.
  """
  tokens = data_point.get("tokens")
  event_mentions = data_point.get("event_mentions", [])
  entity_mentions = data_point.get("entity_mentions", [])

  if not tokens:
    raise ValueError("data_point must contain 'tokens' list")

  def _clean_space_punct(t: str) -> str:
    t = re.sub(r"\s+([,\.\?\!;:%])", r"\1", t)
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"\s+\)", ")", t)
    t = re.sub(r"\s+\"", '"', t)
    t = re.sub(r'\"\s+', '"', t)
    return re.sub(r"\s+", " ", t).strip()

  # collect unique trigger spans sorted left-to-right
  spans = []
  seen = set()
  for ev in event_mentions:
    trig = ev.get("trigger")
    if not trig:
      continue
    try:
      s = int(trig.get("start"))
      e = int(trig.get("end"))
    except Exception:
      continue
    if s < 0 or e <= s or s >= len(tokens):
      continue
    e = min(e, len(tokens))
    if (s, e) not in seen:
      spans.append((s, e))
      seen.add((s, e))

  spans = sorted(spans)

  # identification input
  plain_text = _clean_space_punct(" ".join(tokens))
  identification_input = f"domain: {ds_key}. argument>: {plain_text}"

  def _get_span_text_from_arg(arg):
    if len(arg) == 0:
      return None
    if 'text' in arg and arg.get('text'):
      return _clean_space_punct(arg.get('text'))
    if 'span' in arg and arg.get('span'):
      return _clean_space_punct(arg.get('span'))
    if 'start' in arg and 'end' in arg:
      try:
        s = int(arg.get('start'))
        e = int(arg.get('end'))
        return _clean_space_punct(" ".join(tokens[s:e]))
      except Exception:
        pass
    if 'entity_id' in arg and entity_mentions:
      eid = arg.get('entity_id')
      for ent in entity_mentions:
        if ent.get('id') == eid or ent.get('entity_id') == eid:
          try:
            s = int(ent.get('start'))
            e = int(ent.get('end'))
            return _clean_space_punct(" ".join(tokens[s:e]))
          except Exception:
            pass
    return None

  # build identification output from all arguments
  all_arg_pairs = []
  for ev in event_mentions:
    args = ev.get('arguments')
    if not args:
      continue
    for arg in args:
      role = arg.get('role') or arg.get('role_type') or arg.get('label') or 'Unknown'
      span_text = _get_span_text_from_arg(arg)
      if span_text:
        all_arg_pairs.append(f"argument>{span_text}>={role}")

  identification_output = None if not all_arg_pairs else " | ".join(all_arg_pairs)
  argument_identification = {'input': identification_input, 'output': identification_output} if identification_output else None

  # per-event extraction records
  extraction_records = []
  for ev_idx, ev in enumerate(event_mentions):
    trig = ev.get('trigger')
    if not trig:
      continue
    args = ev.get('arguments')
    if not args:
      # per requirement: skip events with no arguments
      continue
    try:
      s = int(trig.get('start'))
      e = int(trig.get('end'))
    except Exception:
      continue
    try:
      sentinel_idx = spans.index((s, e))
    except ValueError:
      sentinel_idx = len(spans)
      spans.append((s, e))
    
    # human-readable event name
    event_type = ev.get('event_type')
  
    human_name = None
    if event_type:
      human_name = event_type_tags.get(ds_key, {}).get(event_type)
      if human_name is None:
        domain_map = event_type_tags.get(ds_key, {})
        human_name = domain_map.get(event_type.lower()) or domain_map.get(event_type.upper())
      if human_name is None:
        alt = event_type.replace(':', '_').replace('/', '_').replace('-', '_')
        human_name = event_type_tags.get(ds_key, {}).get(alt)
      if human_name is None:
        for dname, dm in event_type_tags.items():
          if event_type in dm:
            human_name = dm.get(event_type)
            break
      if human_name is None:
        human_name = event_type
    else:
      human_name = "UnknownEvent"

    # roles from patterns or fallback to seen roles
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

    if not roles:
      seen_roles = []
      for a in args:
        r = a.get('role') or a.get('role_type') or a.get('label') or 'Unknown'
        if r and r not in seen_roles:
          seen_roles.append(r)
      roles = seen_roles

    # build sentence with only this trigger marked
    parts = []
    i = 0
    while i < len(tokens):
      if i == s:
        span_text = _clean_space_punct(" ".join(tokens[s:e]))
        parts.append(f"trigger {sentinel_idx+1}> {span_text}>")
        i = e
      else:
        parts.append(tokens[i])
        i += 1

    sentence_with_trigger = _clean_space_punct(" ".join(parts))
    roles_str = " | ".join([f"={r}" for r in roles]) if roles else ""
    
    if use_human_readable:
      extraction_input = f"domain: {ds_key}. extract arguments {roles_str} for event {human_name} of trigger {sentinel_idx+1}> {span_text}>: {sentence_with_trigger}"
    else:
      extraction_input = f"domain: {ds_key}. extract arguments {roles_str} for event {event_type} of trigger {sentinel_idx+1}> {span_text}>: {sentence_with_trigger}"

    # build extraction output
    out_pairs = []
    for role in roles:
      found_span = None
      for a in args:
        a_role = a.get('role') or a.get('role_type') or a.get('label')
        if a_role == role:
          st = _get_span_text_from_arg(a)
          if st:
            found_span = st
            break
      if found_span:
        out_pairs.append(f"argument> {found_span}>={role}")
      else:
        out_pairs.append(f"None={role}")
    if use_human_readable:
      extraction_output = f"arguments for event {human_name} of trigger {sentinel_idx+1}> {span_text}>: " + " | ".join(out_pairs)
    else:
      extraction_output = f"arguments for event {event_type} of trigger {sentinel_idx+1}> {span_text}>: " + " | ".join(out_pairs) 

    extraction_records.append({
      'event_id': ev.get('id', ev_idx),
      'input': extraction_input,
      'output': extraction_output
    })

  if not extraction_records:
    return None, None
  return argument_identification, extraction_records




def get_dataset_instances(MAIN_ROOT, ds_key, split_group="split1", splits=None, max_per_split=None):
  """
  Build train/val/test instances for the supported tasks for one dataset.

  Returns a dict with keys:
    - 'trigger_identification', 'trigger_classification', 'argument_extraction', 'argument_identification'
  Each value is a dict with keys 'train','val','test' mapping to lists of
  {'input':..., 'output':...} dicts. Argument tasks include an optional
  'event_id' field when available.
  """
  if splits is None:
    splits = {"train": "train.json", "val": "dev.json", "test": "test.json"}

  tasks = {
    'trigger_identification': {'train': [], 'val': [], 'test': []},
    'trigger_classification': {'train': [], 'val': [], 'test': []},
    'argument_extraction': {'train': [], 'val': [], 'test': []},
    'argument_identification': {'train': [], 'val': [], 'test': []},
  }

  for split_name, split_file in splits.items():
    print('split_file', split_file)
    file_path = os.path.join(MAIN_ROOT, ds_key, split_group, split_file)
    if not os.path.exists(file_path):
      print(f"Warning: missing {ds_key}/{split_group}/{split_file}, skipping")
      continue
    with open(file_path, 'r', encoding='utf-8') as f:
      data = [json.loads(line) for line in f]
    if max_per_split:
      data = data[:max_per_split]
    print(f"  Loaded {len(data)} instances")

    for item in data:
      # Trigger tasks: require event_mentions
      try:
        trig_ann = create_trigger_identification_annotation(item, ds_key=ds_key)
      except Exception:
        trig_ann = None
      # if trigger annotation produced examples, append them
      if trig_ann:
        ident = trig_ann.get('identification')
        clas = trig_ann.get('classification')
        if ident:
          tasks['trigger_identification'][split_name].append({'input': ident['input'], 'output': ident['output']})
        if clas:
          tasks['trigger_classification'][split_name].append({'input': clas['input'], 'output': clas['output']})
        #print(f"    trigger_classification: {len(tasks['trigger_classification'][split_name])} instances")
        #print(f"    trigger_identification: {len(tasks['trigger_identification'][split_name])} instances")

      # Argument tasks: use the dedicated function to get identification and extraction pairs
      try:
        argument_identification, argument_extraction_list = create_argument_extraction_annotation(item, ds_key=ds_key)
      except Exception:
        argument_identification, argument_extraction_list = None, None

      if argument_extraction_list:
        tasks['argument_extraction'][split_name].extend(argument_extraction_list)
      if argument_identification:
        tasks['argument_identification'][split_name].append(argument_identification)
        #print(f"    argument_extraction: {len(tasks['argument_extraction'][split_name])} instances")
        #print(f"    argument_identification: {len(tasks['argument_identification'][split_name])} instances")
        
  return tasks
      
if __name__ == "__main__":  
  MAIN_ROOT = "/nfs/data/debi5729/processed_data"
  
  SPLITS = {
    "train": "train.json",
    "val": "dev.json",
    "test": "test.json"
  }

  datasets =  ['geneva', 'genia2013', 'm2e2', 'rams', 'wikievents', 'casie']
  
  for ds_key in datasets:
    tasks = get_dataset_instances(MAIN_ROOT, ds_key, split_group="split1", splits=SPLITS, max_per_split=None)
    print("Data set", ds_key)
    for task_name, split_dict in tasks.items():
        print(f"  Task: {task_name}")
        for split_name, instances in split_dict.items():
            print(f"    {split_name}: {len(instances)} instances")  
    tasks = get_dataset_instances(MAIN_ROOT, ds_key, split_group="split1", splits=SPLITS, max_per_split=5)
    # print examples
    for task_name, split_dict in tasks.items():
        print(f"  Task: {task_name}")
        for split_name, instances in split_dict.items():
            print(f"    {split_name}: {len(instances)} instances")
            for instance in instances:
                print('Input: ' + instance['input'])
                print('Output: ' + instance['output'])
                print()