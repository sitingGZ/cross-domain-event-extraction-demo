import re
from typing import List, Tuple, Dict
from pattern_tagprime import  patterns
import os
import json



def _clean(s: str) -> str:
	return re.sub(r"\s+", " ", s.strip())


def parse_triggers_from_tagged(source_text: str, tagged_text: str, task_prompt = "Identify trigger words.") -> List[Tuple[str, Tuple[int, int]]]:
	"""Extract trigger span texts and offsets from a tagged sentence.

	Example:
		>>> source = "Domain: geneva. Identify trigger words. China has produced and deployed a wide range of ballistic missiles..."
		>>> tagged = "China has trigger> produced> and trigger> deployed> a wide range of ballistic missiles..."
		>>> parse_triggers_from_tagged(source, tagged)
		[('produced', (29, 37)), ('deployed', (46, 54))]
	"""
	if not tagged_text:
		return []

	# Extract actual text content from source (remove domain and task prompt prefix)
	source_clean = source_text
	# Look for pattern "Domain: xxx. <task prompt> <actual text>"
	# The actual text starts after the second sentence/period
	parts = source_text.split('. ', 2)
	if len(parts) >= 3:
		source_clean = parts[2].strip()
	elif len(parts) == 2:
		source_clean = parts[1].strip()

	spans = []
	# parse the pattern trigger> {span text}> and return all tagged spans texts with offsets in the cleaned source text
	for m in re.finditer(r"trigger>\s*(.+?)\s*>", tagged_text, flags=re.DOTALL):
		span = _clean(m.group(1))
		if not span:
			continue
		# find the span in the source_clean text to get offsets
		start = source_clean.find(span)
		if start >= 0:
			end = start + len(span) - 1
			spans.append((span, (start, end)))
		else:
			# Span not found - return with empty tuple for offsets
			spans.append((span, ()))
	
	return spans


def parse_tc_pairs(ds_key: str, text: str, return_offsets: bool = False) -> List[Tuple[str, str]]:
	"""Parse trigger classification string like:
	'trigger> produced>=Manufacturing | trigger> deployed>=Arranging'

	By default returns list of (trigger_span, class) pairs.
	If `return_offsets=True` returns list of (trigger_span, class, start, end)
	where start/end are character offsets for the span (inclusive).
	"""
	if not text:
		return [], 0, 0

	unrecognized_types = []
	total_predicted_types = 0

	#recognized_types = event_type_tags[ds_key] if ds_key in event_type_tags else set()
	recognized_types = patterns[ds_key]

	def _strip_trigger_prompt(s: str) -> str:
		"""Remove leading prompt text before the first 'trigger>' occurrence."""
		if not s:
			return s
		lower = s.lower()
		idx = lower.find('trigger>')
		if idx >= 0:
			return s[idx:].strip()
		return s

	# If offsets requested, find matches and also compute counts
	if return_offsets:
		matches = []
		txt = _strip_trigger_prompt(text)
		for m in re.finditer(r"trigger>\s*(?P<span>.+?)\s*>=\s*(?P<class>[^|<]+)", txt, flags=re.DOTALL):
			span_raw = m.group('span')
			cls_raw = m.group('class')
			span = _clean(span_raw)
			cls = _clean(cls_raw)
			start = m.start('span')
			end = m.end('span') - 1
			matches.append((span, cls, start, end))
			total_predicted_types += 1
			if cls not in recognized_types:
				unrecognized_types.append(cls)
		return matches, unrecognized_types, total_predicted_types

	# original behavior (no offsets): split on '|' and extract pairs per part
	pairs = []
	txt = _strip_trigger_prompt(text)
	parts = re.split(r"\s*\|\s*", txt)
	for p in parts:
		p = p.strip()
		if not p:
			continue
		# try strict pattern first
		m = re.search(r"trigger>\s*(.+?)\s*>=\s*(.+)$", p)
		if m:
			span = _clean(m.group(1))
			cls = _clean(m.group(2))
			pairs.append((span, cls))
			continue
		# fallback: split on '=' and attempt to locate 'trigger>' in the left side
		if '=' in p:
			left, right = p.split('=', 1)
			# extract span after the last 'trigger>' occurrence if present
			lm = re.search(r"trigger>\s*(.+)$", left)
			if lm:
				span = _clean(lm.group(1))
			else:
				# if left contains 'none' (possibly with surrounding text), treat as None
				if left.strip().lower().startswith('none'):
					span = None
				else:
					span = _clean(left)
			cls = _clean(right)
			pairs.append((span, cls))
			continue
	# dedupe by span (keep first) and compute recognition counts
	seen = set()
	out = []
	for s, c in pairs:
		key = (s, c)
		if s not in seen:
			seen.add(s)
			out.append((s, c))
			total_predicted_types += 1
			if c not in recognized_types:
				unrecognized_types.append(c)
	return out, unrecognized_types, total_predicted_types


def parse_argument_identification_pairs(text: str) -> List[Tuple[str, str]]:
	"""Parse argument strings like:
	'argument>China>=Producer | argument>a wide range...>=Product | None=Role'

	Returns list of (span_or_None, role) pairs. span is None for entries like 'None=Role'.
	"""
	if not text:
		return []

	def _strip_argument_prompt(s: str) -> str:
		"""Remove leading prompt text before the actual argument pairs.

		Handles patterns like:
		- 'trigger> xxx>=Type: argument>...'
		- 'extract arguments ...: ...'
		- general case: slice from first occurrence of 'argument>' or 'None='
		"""
		if not s:
			return s
		lower = s.lower()
		
		# Check for trigger prefix pattern "trigger> xxx>=Type: "
		if 'trigger>' in lower:
			colon_idx = s.find(':', s.find('trigger>'))
			if colon_idx >= 0:
				return s[colon_idx + 1:].strip()
		
		# patterns that usually have a colon before the pairs
		for key in ('extract arguments', 'argument>'):
			idx = lower.find(key)
			if idx >= 0:
				# try to find colon after the pattern (for extract arguments)
				if key == 'extract arguments':
					colon = s.find(':', idx)
					if colon >= 0:
						return s[colon + 1:].strip()
				# if no colon or already 'argument>', just return from that point
				if key == 'argument>':
					return s[idx:].strip()
		
		# otherwise slice from the first 'argument>' or 'none=' occurrence
		candidates = []
		for key in ('argument>', 'none='):
			i = lower.find(key)
			if i >= 0:
				candidates.append(i)
		if candidates:
			pos = min(candidates)
			return s[pos:].strip()
		return s

	# strip prompt-like prefix so parser only sees the pairs
	text = _strip_argument_prompt(text)
	parts = re.split(r"\s*\|\s*", text)
	out: List[Tuple[str, str]] = []
	for p in parts:
		p = p.strip()
		if not p:
			continue
		# None=Role pattern
		m_none = re.match(r"None\s*=\s*(.+)$", p)
		if m_none:
			role = _clean(m_none.group(1))
			out.append((None, role))
			continue
		# argument>span>=Role or argument> span = Role
		m = re.search(r"argument>\s*(.+?)\s*>=\s*(.+)$", p)
		if m:
			span = _clean(m.group(1))
			role = _clean(m.group(2))
			out.append((span, role))
			continue
		# fallback: try split on '=' (span left or 'argument>span')
		if '=' in p:
			left, right = p.split('=', 1)
			role = _clean(right)
			lm = re.search(r"argument>\s*(.+)$", left)
			span = _clean(lm.group(1)) if lm else _clean(left)
			out.append((span, role))
			continue
	# dedupe by (span,role) preserving order
	seen = set()
	res = []
	for s, r in out:
		key = (s, r)
		if key not in seen:
			seen.add(key)
			res.append((s, r))
	return res


def parse_e2e_trigger_detection_predictions(prediction_str, source_input):
	"""
	Parse trigger word predictions and find their offsets in the source input.

	Args:
		prediction_str: String containing trigger predictions in the format:
			"trigger> data breach>=Attack:Databreach | trigger> the breach>=Attack:Databreach | ..."
		source_input: The source text where triggers should be found, starting with:
			"Domain: casie. Classify trigger types end-to-end. The Intercontinental Hotels Group data breach..."

	Returns:
		List of tuples: [(trigger_word, event_type, (start_offset, end_offset)), ...]

	Example:
		>>> prediction = "trigger> data breach>=Attack:Databreach | trigger> steal>=Attack:Databreach"
		>>> source = "Domain: casie. Classify trigger types end-to-end. The data breach occurred when attackers steal information."
		>>> parse_e2e_trigger_detection_predictions(prediction, source)
		[('data breach', 'Attack:Databreach', (29, 40)), ('steal', 'Attack:Databreach', (69, 74))]
	"""
	results = []

	# Extract the actual text content from source input (remove domain and task prompt)
	# Format: "Domain: casie. <task prompt>. The actual text here..."
	text_content = source_input
	parts = source_input.split('. ', 2)
	if len(parts) >= 3:
		text_content = parts[2].strip()
	elif len(parts) == 2:
		text_content = parts[1].strip()

	# Parse prediction string to extract trigger words and their types
	# Format: "trigger> word>=Type | trigger> word2>=Type2 | ..."
	trigger_items = prediction_str.split("|")

	# Track found trigger positions to handle duplicates
	found_positions = set()

	for item in trigger_items:
		item = item.strip()
		if not item or "trigger>" not in item:
			continue

		# Extract trigger word and type
		# Format: "trigger> word>=Type"
		try:
			# Remove "trigger>" prefix
			content = item.split("trigger>", 1)[1].strip()

			# Split by ">=" to get word and type
			if ">=" in content:
				trigger_word, event_type = content.split(">=", 1)
				trigger_word = trigger_word.strip()
				event_type = event_type.strip()
			else:
				continue

			# Find all occurrences of the trigger word in the text
			# Use case-sensitive search
			start_idx = 0
			found = False
			while True:
				# Find next occurrence
				pos = text_content.find(trigger_word, start_idx)
				if pos == -1:
					break

				# Check if this position hasn't been used yet
				end_pos = pos + len(trigger_word)
				position_key = (trigger_word, pos, end_pos)

				if position_key not in found_positions:
					# Calculate offset in the original source_input
					# Need to account for the prefix "Domain: xxx. <task>. "
					prefix_len = 0
					parts = source_input.split('. ', 2)
					if len(parts) >= 3:
						prefix_len = len(parts[0]) + len(parts[1]) + 4  # +4 for ". " after each part
					elif len(parts) == 2:
						prefix_len = len(parts[0]) + 2  # +2 for ". "
					
					actual_start = prefix_len + pos
					actual_end = prefix_len + end_pos

					results.append((trigger_word, event_type, (actual_start, actual_end)))
					found_positions.add(position_key)
					found = True
					break  # Only find the first unused occurrence for this trigger

				start_idx = pos + 1
			
			# If trigger word not found, return with empty tuple for offsets
			if not found:
				results.append((trigger_word, event_type, ()))

		except Exception as e:
			# Skip malformed items
			print(f"Warning: Failed to parse item '{item}': {e}")
			continue

	return results


def parse_argument_extraction_pipeline_predictions(doc_id, prediction_str, source_input):
	"""
	Parse argument extraction predictions and find their offsets in the source input.
	
	Args:
		prediction_str: String containing argument predictions in the format:
			"trigger> produced>=Manufacturing: argument> China>=Producer | argument> a wide range...>=Product | None=Role"
		source_input: The source text where arguments should be found, starting with:
			"Domain: geneva. Extract arguments for a specific event. argument> Producer | Product | ... for trigger> produced>=Manufacturing: China has produced..."
	
	Returns:
		Dictionary with doc_id as key and list of tuples as value:
		[(span_text, argument_role, (start_offset, end_offset)), ...]
		If span not found, returns empty tuple () for offsets: [(span_text, argument_role, ()), ...]
		Ignores "None" entries (returns only actual argument> items)
	
	Example:
		>>> prediction = "trigger> produced>=Manufacturing: argument> China>=Producer | argument> a wide range of ballistic missiles>=Product | None=Resource"
		>>> source = "Domain: geneva. Extract arguments for a specific event. argument> Producer | Product | Resource for trigger> produced>=Manufacturing: China has produced a wide range of ballistic missiles."
		>>> parse_argument_extraction_pipeline_predictions("doc1", prediction, source)
		{'doc1': [('China', 'Producer', (start, end)), ('a wide range of ballistic missiles', 'Product', (start, end))]}
		
		If span not found in source:
		>>> parse_argument_extraction_pipeline_predictions("doc1", prediction, "Domain: geneva. Extract arguments... no Rwanda here")
		{'doc1': [('Rwanda', 'Place', ())]}
	"""
	results = []
	
	# Extract the actual text content from source input (remove domain and task prompt)
	# source = "Domain: geneva. Extract arguments for a specific event. argument> Producer | Product | Resource for trigger> produced>=Manufacturing: China has produced a wide range of ballistic missiles."
	# Split by the second colon to separate the prompt from the actual text
	#text_content = source_input.split(": ", 2)[2].strip()
	
	# Find the argument parts after the first colon in the prediction string
	try:
		argument_part = prediction_str.split(": ", 1)[1].strip()
	except IndexError:
		argument_part = ""
		print(f"Warning: No argument part found in prediction string {prediction_str}.")
		return {doc_id: results}
	
	# Split by '|' to get individual argument predictions
	argument_items = argument_part.split(" | ")
	
	# Find each argument prediction
	for item in argument_items:
		item = item.strip()
		if not item or "argument>" not in item:
			continue
		#if item.lower().startswith("none="):
		if 'none=' in item.lower():
			continue  # Skip None entries
		#elif item.startswith("argument>"):
		if 'argument>' in item:
			content = item.split("argument>")[1].strip()
			if ">=" in content:
				span_text, role = content.split(">=", 1)
				span_text = span_text.strip()
				role = role.strip()
				
				# Find offset in source text
				pos = source_input.find(span_text)
				if pos != -1:
					# Calculate actual offset in source_input
					# Need to account for the prefix "Domain: xxx. <task>. "
					prefix_len = 0
					parts = source_input.split('. ', 2)
					if len(parts) >= 3:
						prefix_len = len(parts[0]) + len(parts[1]) + 4  # +4 for ". " after each part
					elif len(parts) == 2:
						prefix_len = len(parts[0]) + 2  # +2 for ". "
					
					actual_offset = (prefix_len + pos, prefix_len + pos + len(span_text))
					results.append((span_text, role, actual_offset))
				else:
					# Span not found - return with empty tuple for offsets
					results.append((span_text, role, ()))
	
	return {doc_id: results}


def parse_e2e_event_extraction_predictions(prediction_str, source_input):
	"""
	Parse end-to-end event extraction predictions with the new delimiter pattern.

	Args:
		prediction_str: String containing e2e predictions in the format:
			"trigger>text>=Type | argument>text>=Role | argument>text>=Role || trigger>text>=Type | argument>text>=Role"
		source_input: The source text where events should be found, starting with:
			"Domain: casie. Event trigger and argument extraction. The actual text here..."

	Returns:
		List of dicts, each containing:
			{
				'trigger': {'text': str, 'type': str, 'offset': (start, end)},
				'arguments': [{'text': str, 'role': str, 'offset': (start, end)}, ...]
			}

	Example:
		>>> prediction = "trigger>exploded>=Attack:Explosion | argument>bomb>=Instrument || trigger>injured>=Injury | argument>victim>=Victim"
		>>> source = "Domain: geneva. Event trigger and argument extraction. The bomb exploded and injured the victim."
		>>> parse_e2e_event_extraction_predictions(prediction, source)
		[
			{
				'trigger': {'text': 'exploded', 'type': 'Attack:Explosion', 'offset': (39, 47)},
				'arguments': [{'text': 'bomb', 'role': 'Instrument', 'offset': (33, 37)}]
			},
			{
				'trigger': {'text': 'injured', 'type': 'Injury', 'offset': (52, 59)},
				'arguments': [{'text': 'victim', 'role': 'Victim', 'offset': (64, 70)}]
			}
		]
	"""
	results = []

	# Extract the actual text content from source input
	# Format: "Domain: xxx. <task prompt>. The actual text here..."
	text_content = source_input
	prefix_len = 0
	
	parts = source_input.split('. ', 2)
	if len(parts) >= 3:
		text_content = parts[2].strip()
		prefix_len = len(parts[0]) + len(parts[1]) + 4  # +4 for ". " after each part
	elif len(parts) == 2:
		text_content = parts[1].strip()
		prefix_len = len(parts[0]) + 2  # +2 for ". "

	# Split by '||' to get individual events
	event_groups = prediction_str.split(" || ")

	# Track used positions to handle overlapping spans
	used_positions = set()

	for event_group in event_groups:
		event_group = event_group.strip()
		if not event_group:
			continue

		# Split by '|' to get trigger and arguments within the event
		components = [comp.strip() for comp in event_group.split(" | ")]

		event_data = {
			'trigger': None,
			'arguments': []
		}

		for comp in components:
			if not comp:
				continue

			# Parse trigger
			#if comp.startswith("trigger>"):
			if 'trigger>' in comp:
				try:
					content = comp.split("trigger>", 1)[1].strip()
					if ">=" in content:
						text, event_type = content.split(">=", 1)
						text = text.strip()
						event_type = event_type.strip()

						# Find offset in source text
						pos = text_content.find(text)
						if pos != -1:
							offset = (pos, pos + len(text))
							if offset not in used_positions:
								# Calculate actual offset in source_input
								actual_offset = (prefix_len + pos, prefix_len + pos + len(text))

								event_data['trigger'] = {
									'text': text,
									'type': event_type,
									'offset': actual_offset
								}
								used_positions.add(offset)
						else:
							# Trigger text not found - use empty tuple for offset
							event_data['trigger'] = {
								'text': text,
								'type': event_type,
								'offset': ()
							}
				except Exception as e:
					print(f"Warning: Failed to parse trigger '{comp}': {e}")
					continue

			# Parse argument
			#elif comp.startswith("argument>"):
			elif 'argument>' in comp:
				try:
					content = comp.split("argument>", 1)[1].strip()
					if ">=" in content:
						text, role = content.split(">=", 1)
						text = text.strip()
						role = role.strip()

						# Skip "None" placeholders
						if text.lower() == "none":
							continue

						# Find offset in source text
						pos = text_content.find(text)
						if pos != -1:
							offset = (pos, pos + len(text))
							# Calculate actual offset in source_input
							actual_offset = (prefix_len + pos, prefix_len + pos + len(text))

							event_data['arguments'].append({
								'text': text,
								'role': role,
								'offset': actual_offset
							})
						else:
							# Argument text not found - use empty tuple for offset
							event_data['arguments'].append({
								'text': text,
								'role': role,
								'offset': ()
							})
				except Exception as e:
					print(f"Warning: Failed to parse argument '{comp}': {e}")
					continue

		# Only add event if it has a valid trigger
		if event_data['trigger']:
			results.append(event_data)

	return results


if __name__ == "__main__":
	# Test trigger classification parsing
	tasks = [
		'trigger_identification',
		'trigger_classification_pipeline', 
		'trigger_classification_e2e',
		'argument_identification_e2e',
		'argument_extraction_pipeline',
		'event_extraction_e2e'
	]
	model_root = "/nfs/work/debi5729"
	split_group = "split1"
	datasets = ["m2e2"]  # Replace with actual dataset keys
	model_dir = f"{model_root}/google-t5-t5-base_split1_{'_'.join(datasets)}_amount_1_e2e_True_full_latest_expressive_prompt"
	test_results_file = os.path.join(model_dir, 'generations', "epoch-40", 'm2e2', 'test.jsonl')
	with open(test_results_file, 'r') as f:
		for task in tasks:
			print(f"=== Results for task: {task} ===")
			for line in f:
				rec = json.loads(line)
				if rec['task'] != task:
					continue
				print(f"Doc id and index: {rec['doc_id']} - {rec['index']}")
				print(f"Input: {rec['source']}")
				print(f"Reference: {rec['reference']}")
				print(f"Output: {rec['prediction']}")

				if task == 'trigger_identification':
					triggers = parse_triggers_from_tagged(rec['source'], rec['prediction'])
					print(f"Parsed prediction triggers: {triggers}")
					trigger_refs = parse_triggers_from_tagged(rec['source'], rec['reference'])
					print(f"Parsed reference triggers: {trigger_refs}")
				elif task == 'trigger_classification_pipeline':
					tc_pairs, unrecog, total = parse_tc_pairs("m2e2", rec['prediction'])
					print(f"Parsed trigger classifications: {tc_pairs} (Unrecognized: {unrecog}/{total})")
					tc_refs, unrecog_refs, total_refs = parse_tc_pairs("m2e2", rec['reference'])
					print(f"Parsed reference trigger classifications: {tc_refs} (Unrecognized: {unrecog_refs}/{total_refs})")
				elif task == 'trigger_classification_e2e':
					e2e_triggers = parse_e2e_trigger_detection_predictions(rec['prediction'], rec['source'])
					print(f"Parsed e2e triggers: {e2e_triggers}")
					e2e_trigger_refs = parse_e2e_trigger_detection_predictions(rec['reference'], rec['source'])
					print(f"Parsed reference e2e triggers: {e2e_trigger_refs}")
                
				elif task == 'argument_identification_e2e':
					arg_pairs = parse_argument_identification_pairs(rec['prediction'])
					print(f"Parsed argument pairs: {arg_pairs}")
					arg_refs = parse_argument_identification_pairs(rec['reference'])
					print(f"Parsed reference argument pairs: {arg_refs}")
				elif task == 'argument_extraction_pipeline':
					arg_extractions = parse_argument_extraction_pipeline_predictions(rec['doc_id'], rec['prediction'], rec['source'])
					print(f"Parsed argument extractions: {arg_extractions}")
					arg_extraction_refs = parse_argument_extraction_pipeline_predictions(rec['doc_id'], rec['reference'], rec['source'])
					print(f"Parsed reference argument extractions: {arg_extraction_refs}")
				elif task == 'event_extraction_e2e':
					e2e_events = parse_e2e_event_extraction_predictions(rec['prediction'], rec['source'])
					print(f"Parsed e2e events: {e2e_events}")
					e2e_event_refs = parse_e2e_event_extraction_predictions(rec['reference'], rec['source'])
					print(f"Parsed reference e2e events: {e2e_event_refs}")
					
				print()
			f.seek(0)   
			
