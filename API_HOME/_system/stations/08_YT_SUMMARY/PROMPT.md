You are building the base layer of a research index of YouTube videos for David Lowe's Theophysics work.
Read the WHOLE transcript below. Answer every question in QUESTIONS exactly and concretely, citing
timestamps ([mm:ss]) for every factual statement about what is said. Do not evaluate yet; that is the
detailed layer's job. If the transcript does not answer a question, say "not in this video".

Return one JSON object:
{"summary": "3-5 sentences",
 "answers": [{"question": "...", "answer": "...", "timestamps": ["mm:ss", ...]}],
 "people_and_sources": [{"name": "...", "role": "cited | quoted | criticized | speaker", "timestamp": "mm:ss"}],
 "topics": ["..."],
 "focus_findings": [{"point": "...", "finding": "...", "timestamps": ["mm:ss"]}]}
