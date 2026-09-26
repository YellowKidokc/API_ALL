# 1. Put 7Q Full Method.xlsx in the same folder as this script.
# 2. Run:
python chi_evaluator_7q.py --input "your_text_or_file.txt"

# Or from Python:
from chi_evaluator_7q import evaluate_text
result = evaluate_text("This is a sample claim to test.")
print(result["truth_score"])