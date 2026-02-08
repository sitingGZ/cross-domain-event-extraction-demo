# imports used by the annotation helpers
import re
from pattern_tagprime import event_type_tags,patterns, role_type_tags
import json
import os

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
    


def create_trigger_identification_annotation(data_point, ds_key="geneva", use_human_readable=False, augument_word_generation=True):
  """
  Produce T5-style sentinel templates for trigger identification and
  classification.

  Returns a dict with keys:
    - 'template_one_input': input with trigger spans replaced by sentinels
    - 'template_one_output': label sequence mapping sentinels to span texts
    - 'template_two_input': same as template_one_input (for classification)
    - 'template_two_output': label sequence mapping sentinels to span=class
 The labels are constructed as
  `trigger {idx}> span_text > ` where
  N = number of spans. For classification, span_text_i is replaced by
  `span_text_i=HumanReadableClass`.
  """
  results = {}
  tokens = data_point.get("tokens")
  event_mentions = data_point.get("event_mentions", [])

  if not tokens:
    raise ValueError("data_point must contain 'tokens' list")

  # collect unique trigger spans sorted left-to-right, trigger words can be multi-word and repeat in text
  spans = []
  #seen = set()
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
    #if (s, e) not in seen:
    spans.append((s, e))
      #seen.add((s, e))

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
      class_labels.append(f"trigger> {span_text}>={human_name}")
    else:
      class_labels.append(f"trigger> {span_text}>={primary if primary else 'Unknown'}")
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
    tagged_parts.append(f"trigger> {span_text}>")
    cursor = e
  if cursor < len(tokens):
    tagged_parts.extend(tokens[cursor:])

  tagged_sentence = _clean_space_punct(" ".join(tagged_parts))
  plain_text = _clean_space_punct(" ".join(tokens))
  template_one_input = f"domain: {ds_key}. trigger>: {plain_text}"
  template_one_output = tagged_sentence
  # Use the plain  text, without tagged parts, for classification input
  #template_two_input = f"domain: {ds_key}. trigger>=type: {tagged_sentence}"
  template_two_input = f"domain: {ds_key}. trigger>=type: {plain_text}"
  results['identification'] = {'input': template_one_input, 'output': template_one_output}
  results['classification'] = {'input': template_two_input, 'output': template_two_output}
  
  if augument_word_generation:
    # template input 
    template_three_input = f"domain: {ds_key}. trigger words: {plain_text}"
    all_trigger_span_texts = [_clean_space_punct(" ".join(tokens[s:e])) for (s,e) in spans]
    template_three_output = " | ".join(all_trigger_span_texts)
    results['identification_augument'] = {'input': template_three_input, 'output': template_three_output}
    
  
  

  # handle no-spans case: create a canonical NO_TRIGGER label if desired
  if not spans:
    #template_one_output = "<extra_id_0> NO_TRIGGER <extra_id_1>"
    #template_two_output = "<extra_id_0> NO_TRIGGER <extra_id_1>"
    return None
  
  else:
    return results
   


def create_event_extraction_e2e_annotation(data_point, ds_key="geneva", use_human_readable=False):
  """
  Create end-to-end event extraction annotation combining triggers and arguments.
  
  Args:
      data_point: Dictionary containing 'tokens', 'event_mentions', 'entity_mentions'
      ds_key: Dataset key (e.g., "geneva", "casie")
      use_human_readable: Whether to use human-readable event/role names
  
  Returns:
      Dict with 'input' and 'output' keys, or None if no events found
      
  Example:
      Input: "domain: geneva. event extraction: The bomb exploded and injured the victim."
      Output: "trigger>exploded>=Attack:Explosion ## argument>bomb>=Instrument ## argument>victim>=Victim | trigger>injured>=Injury ## argument>victim>=Victim"
      
  Pattern explanation:
      - '##' separates trigger from arguments and arguments from each other within an event
      - '|' separates different events
      - This makes parsing unambiguous: split by '|' for events, then by '##' for components
  """
  tokens = data_point.get("tokens")
  event_mentions = data_point.get("event_mentions", [])
  entity_mentions = data_point.get("entity_mentions", [])
  
  if not tokens:
    raise ValueError("data_point must contain 'tokens' list")
  
  if not event_mentions:
    return None
  
  def _clean_space_punct(t: str) -> str:
    t = re.sub(r"\s+([,\.\?\!;:%])", r"\1", t)
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"\s+\)", ")", t)
    t = re.sub(r"\s+\"", '"', t)
    t = re.sub(r'\"\s+', '"', t)
    return re.sub(r"\s+", " ", t).strip()
  
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
  
  plain_text = _clean_space_punct(" ".join(tokens))
  e2e_input = f"domain: {ds_key}. event extraction: {plain_text}"
  
  # Collect unique trigger spans sorted left-to-right, trigger words can be multi-word and repeat in text
  spans = []
  span_to_event = {}  # Map (start, end) to event mention
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
    span_key = (s, e)
    if span_key not in span_to_event:
      spans.append(span_key)
      span_to_event[span_key] = ev
  
  spans = sorted(spans)
  
  # Build output for each event following the sorted order of trigger spans
  event_outputs = []
  for span_key in spans:
    s, e = span_key
    ev = span_to_event[span_key]
    
    trigger_text = _clean_space_punct(" ".join(tokens[s:e]))
    event_type = ev.get("event_type")
    
    # Get human-readable event type if requested
    if use_human_readable:
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
      event_type_str = human_name if human_name else (event_type if event_type else "Unknown")
    else:
      event_type_str = event_type if event_type else "Unknown"
    
    # Start with trigger
    event_parts = [f"trigger>{trigger_text}>={event_type_str}"]
    
    # Add arguments
    args = ev.get("arguments", [])
    for arg in args:
      role = arg.get('role') or arg.get('role_type') or arg.get('label') or 'Unknown'
      span_text = _get_span_text_from_arg(arg)
      if span_text:
        event_parts.append(f"argument>{span_text}>={role}")
    
    # Join trigger and arguments with '##' separator for clear delimitation
    event_outputs.append(" ## ".join(event_parts))
  
  if not event_outputs:
    return None
  
  # Join all events with " | "
  e2e_output = " | ".join(event_outputs)
  
  return {
    'input': e2e_input,
    'output': e2e_output
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
        parts.append(f"trigger> {span_text}>")
        i = e
      else:
        parts.append(tokens[i])
        i += 1

    sentence_with_trigger = _clean_space_punct(" ".join(parts))
    roles_str = " ## ".join([f"={r}" for r in roles]) if roles else ""
    
    if use_human_readable:
      #extraction_input = f"domain: {ds_key}. extract arguments {roles_str} for event {human_name} of trigger> {span_text}>: {sentence_with_trigger}"
      extraction_input = f"domain: {ds_key}. trigger> {span_text}>={human_name} | argument> {roles_str}: {plain_text}"
    else:
      extraction_input = f"domain: {ds_key}. trigger> {span_text}>={event_type} | argument> {roles_str}: {plain_text}"

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
      extraction_output = f"trigger> {span_text}>={human_name} | " + " ## ".join(out_pairs)
    else:
      extraction_output = f"trigger> {span_text}>={event_type} | " + " ## ".join(out_pairs) 

    extraction_records.append({
      'event_id': ev.get('id', ev_idx),
      'input': extraction_input,
      'output': extraction_output
    })

  if not extraction_records:
    return None, None
  return argument_identification, extraction_records

def create_argument_extraction_annotation_different(data_point, ds_key="geneva", use_human_readable=False):
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
        parts.append(f"trigger> {span_text}>")
        i = e
      else:
        parts.append(tokens[i])
        i += 1

    sentence_with_trigger = _clean_space_punct(" ".join(parts))
    roles_str = " | ".join([f"={r}" for r in roles]) if roles else ""
    
    if use_human_readable:
      #extraction_input = f"domain: {ds_key}. extract arguments {roles_str} for event {human_name} of trigger> {span_text}>: {sentence_with_trigger}"
      extraction_input = f"domain: {ds_key}. argument> {roles_str} for trigger> {span_text}>={human_name}: {plain_text}"
    else:
      extraction_input = f"domain: {ds_key}. argument> {roles_str} for trigger> {span_text}>={event_type}: {plain_text}"

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
      extraction_output = f"trigger> {span_text}>={human_name}: " + " | ".join(out_pairs)
    else:
      extraction_output = f"trigger> {span_text}>={event_type}: " + " | ".join(out_pairs) 

    extraction_records.append({
      'event_id': ev.get('id', ev_idx),
      'input': extraction_input,
      'output': extraction_output
    })

  if not extraction_records:
    return None, None
  return argument_identification, extraction_records

def get_dataset_instances_no_index(MAIN_ROOT, ds_key, tasks = None, split_group="split1", splits=None, max_per_split=None, augument_word_generation=True):
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
    
  if tasks is None: 

    tasks = {
    'trigger_identification': {'train': [], 'val': [], 'test': []},
    'trigger_classification': {'train': [], 'val': [], 'test': []},
    'argument_extraction': {'train': [], 'val': [], 'test': []},
    'argument_identification': {'train': [], 'val': [], 'test': []},
    'trigger_identification_augument': {'train': [], 'val': [], 'test': []}
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
        trig_ann = create_trigger_identification_annotation(item, ds_key=ds_key, augument_word_generation=augument_word_generation)
      except Exception:
        trig_ann = None
      # if trigger annotation produced examples, append them
      if trig_ann:
        ident = trig_ann.get('identification')
        clas = trig_ann.get('classification')
        ident_aug = trig_ann.get('identification_augument')
        if ident_aug:
          tasks['trigger_identification_augument'][split_name].append({'input': ident_aug['input'], 'output': ident_aug['output']})
        if ident:
          tasks['trigger_identification'][split_name].append({'input': ident['input'], 'output': ident['output']})
        if clas:
          tasks['trigger_classification'][split_name].append({'input': clas['input'], 'output': clas['output']})
        #print(f"    trigger_classification: {len(tasks['trigger_classification'][split_name])} instances")
        #print(f"    trigger_identification: {len(tasks['trigger_identification'][split_name])} instances")

      # Argument tasks: use the dedicated function to get identification and extraction pairs
      try:
        argument_identification, argument_extraction_list = create_argument_extraction_annotation_different(item, ds_key=ds_key)
      except Exception:
        argument_identification, argument_extraction_list = None, None

      if argument_extraction_list:
        tasks['argument_extraction'][split_name].extend(argument_extraction_list)
      if argument_identification:
        tasks['argument_identification'][split_name].append(argument_identification)
        #print(f"    argument_extraction: {len(tasks['argument_extraction'][split_name])} instances")
        #print(f"    argument_identification: {len(tasks['argument_identification'][split_name])} instances")
        
  return tasks

def get_dataset_instances_no_index_e2e(MAIN_ROOT, ds_key, split_group="split1", splits=None, max_per_split=None):
  """
  Build train/val/test instances for end-to-end event extraction for one dataset.

  Returns a dict with keys:
    - 'event_extraction_e2e'
  Each value is a dict with keys 'train','val','test' mapping to lists of
  {'input':..., 'output':...} dicts.
  """ 
  if splits is None:
    splits = {"train": "train.json", "val": "dev.json", "test": "test.json"}
    
  tasks = {
      'event_extraction_e2e': {'train': [], 'val': [], 'test': []}
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
      try:
        e2e_ann = create_event_extraction_e2e_annotation(item, ds_key=ds_key)
      except Exception:
        e2e_ann = None
      if e2e_ann:
        tasks['event_extraction_e2e'][split_name].append({'input': e2e_ann['input'], 'output': e2e_ann['output']})
  return tasks

def get_dataset_instances_no_index_all(MAIN_ROOT, ds_key, split_group="split1", splits=None, max_per_split=None, augument_word_generation=True, e2e=True):
  """
  Build all task instances for one dataset.

  Returns a dict with keys:
    - 'trigger_identification', 'trigger_classification', 'argument_extraction', 'argument_identification', 'event_extraction_e2e'
  Each value is a dict with keys 'train','val','test' mapping to lists of
  {'input':..., 'output':...} dicts. Argument tasks include an optional
  'event_id' field when available.
  """
  tasks = get_dataset_instances_no_index(MAIN_ROOT, ds_key, split_group=split_group, splits=splits, max_per_split=max_per_split, augument_word_generation=augument_word_generation)
  e2e_tasks = get_dataset_instances_no_index_e2e(MAIN_ROOT, ds_key, split_group=split_group, splits=splits, max_per_split=max_per_split)
  tasks.update(e2e_tasks)
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
      tasks = get_dataset_instances_no_index(MAIN_ROOT, ds_key, split_group="split1", splits=SPLITS, augument_word_generation=True)
      for task_name, split_dict in tasks.items():
          for split_name, records in split_dict.items():
              print(f"{ds_key} {task_name} {split_name}: {len(records)} instances")
              # print one example
              if records:
                  print(f"  Example input: {records[0]['input']}")
                  print(f"  Example output: {records[0]['output']}")
              print('-----------')
      # E2E task
      e2e_tasks = get_dataset_instances_no_index_e2e(MAIN_ROOT, ds_key, split_group="split1", splits=SPLITS)
      for task_name, split_dict in e2e_tasks.items():
          for split_name, records in split_dict.items():
              print(f"{ds_key} {task_name} {split_name}: {len(records)} instances")
              # print one example
              if records:
                  print(f"  Example input: {records[0]['input']}")
                  print(f"  Example output: {records[0]['output']}")
              print('-----------')
      