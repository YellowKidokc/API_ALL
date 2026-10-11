You score what each sentence DOES in context (its mechanism), not the words it uses.
For every sentence id listed in IDS, return 9 integers from -2 to +2 in this fixed order:
love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self_control.
-2 clear anti-fruit · -1 leans anti · 0 neutral or not engaged · +1 leans toward the fruit · +2 clear embodiment.
Sarcasm, a quoted opponent, correction given gently, a hard truth told for the reader's good (that is love even
with no "love" word): judge the mechanism. Vocabulary is not character evidence.

Give a reason ONLY when |value| = 2, or when your sign disagrees with the LEXICON HINT for that fruit
(the hint lists the fruit words found in the sentence). Keep reasons under 15 words.
Score every id in IDS and nothing else. You see the whole paper for context.

Return: {"sentences": [{"id": "S001", "v": [0,0,0,0,0,0,0,0,0], "why": {"love": "..."}}]}
