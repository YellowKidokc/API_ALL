# STORY station V2: hook, sequence, coherence, then memorable lines

Replaces `API_DEEP\STORIES\PROMPT.md` (V1 only pulled stories out of a paper). David's spec, 2026-09-24:
check whether a paper, and then its whole series, has the right hook and sequence and holds together.
**Only if it does**, write the most memorable line possible for every paragraph.

Runs in three passes. Each pass is its own API call and saves its own JSON, so a rerun skips finished passes.

---

## Pass 1: one paper (per paper)

Input: the paper's full text, paragraphs numbered `P01, P02 ...` by the runner (not the model).

Check:
1. **Hook**: quote the opening 1-3 sentences. Does the opening raise a question the reader needs answered?
   Give a score of 1-5. If a stronger hook sits deeper in the paper, quote it and give its paragraph number.
   Offer one rewrite of the opening line, or none if the current one scores 5.
2. **Sequence**: give every paragraph a role: `hook | setup | tension | turn | evidence | payoff | callback | aside`.
   Flag any paragraph that comes before what it depends on, or after the point it was needed.
   Propose a new order only if it changes something (list of paragraph ids).
3. **Coherence**: state the through-line in one sentence. For every paragraph, say whether it serves the
   through-line: `yes | partly | no`, with a reason for anything other than yes.
   List drift points and any contradiction with an earlier paragraph (both ids, quoted).
4. **Landing**: does the ending pay off the hook? `yes | partly | no`, with a reason.

Verdict: `COHERENT` (ready for lines) | `FIXABLE` (list the fixes, at most 5, most important first) | `NOT_COHERENT`.

```json
{"paper": "", "hook": {"quote": "", "score": 1, "better_hook": {"para": "P07", "quote": ""}, "rewrite": ""},
 "through_line": "",
 "paragraphs": [{"id": "P01", "role": "hook", "serves": "yes", "reason": "", "out_of_order": false}],
 "proposed_order": [], "drift": [], "contradictions": [{"a": "P03", "b": "P11", "quote_a": "", "quote_b": "", "note": ""}],
 "landing": {"verdict": "yes", "reason": ""},
 "verdict": "COHERENT", "fixes": []}
```

## Pass 2: the series (per series, after every paper has a Pass 1)

Input: the series order, and for every paper its Pass 1 JSON plus its first and last paragraph (not the full text).

Check:
1. The series through-line in one sentence, and each paper's role in it.
2. **Handoffs**: does paper N's ending set up paper N+1's opening? Score each seam from 1 to 5.
3. Beats that repeat (the same point made in two papers) and beats the series needs but no paper makes.
4. Contradictions across papers (paper ids and quotes).
5. A new reading order only if it would change something.

Verdict: `COHERENT | FIXABLE | NOT_COHERENT`, with the fixes listed.

## Pass 3: memorable lines (gated)

Runs only when the series verdict is `COHERENT` and the paper's verdict is `COHERENT`.
David can override the gate with `--force-lines`. Otherwise the output is the fix list, not lines.

For **every paragraph**, write **one line** (target 12 words or fewer) that someone would still remember a week later:
- it says the paragraph's actual point, not a slogan about the topic
- it uses a concrete image, a contrast or reversal, and a rhythm that can be said aloud
- it claims nothing the paragraph doesn't support (no overclaiming)
- no clichés and no rhetorical questions, and no two lines in a paper share an opening word or structure

Also write, for each paper, a **signature line** (3 candidates, best first) and one line for the whole series.
Hand in the best line only, not variations. The original text is never changed: lines are stored beside the paper
and rendered as a pull-quote above each paragraph in a separate `..._LINES.md` copy.

```json
{"paper": "", "lines": [{"id": "P01", "line": "", "words": 9}],
 "signature": ["", "", ""], "series_line": ""}
```

Cost note: a 40-paragraph paper is about one long call. Send Pass 3 in groups of 15 paragraphs,
with the through-line and previous lines included, so later lines don't repeat earlier ones.
