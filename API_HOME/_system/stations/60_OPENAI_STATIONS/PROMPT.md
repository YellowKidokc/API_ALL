# 60_OPENAI_STATIONS

The 23 `api_call_NN` prompts from Open-AI-CALL-OBS-Plugin (copied into `prompts/NN_TITLE/prompt.txt`; edit them there).
They are grouped into bundles (`bundles.json`) so one whole-document call answers several stations; each station still
gets its own goal id (API-60.NN) and its own saved output. Which stations deserve their own permanent menu number
is still David's decision; until then they live here, selectable with `--stations 05,17` or `--bundle grading`.
