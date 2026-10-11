# TASK: synthesize a video index

The INPUT is the merged result of indexing one video in chunks: its title, the
opening of the transcript, the chunk summaries, and every argument, speaker and
person the chunk calls found. The chunks could not see each other, so there
are duplicates and anonymous labels. Clean it up.

1. **summary**: one 4-6 sentence summary of the whole video. Name the speakers
   and the video's overall case. Do not say "this chunk".
2. **speakers**: who actually speaks, with real names where the title,
   transcript or context allow ("Guest" or "unknown host" only as a last
   resort). Auto-captions garble names. A wrong identity is worse than none:
   append "(?)" to any name you infer rather than read directly. Watch family
   and author confusion; a guest who says "my dad wrote this book" is not the
   book's author. Keep each speaker's religious, metaphysical and scientific
   positions from the chunks.
3. **people_aliases**: map every variant or anonymous label to one canonical
   name, e.g. {"Steven Meyer": "Stephen Meyer", "Plantinga": "Alvin
   Plantinga", "Guest": "Sean McDowell"}. Cover the speaker labels used on
   arguments too ("unknown guest", "host"). Only include entries that change.
   Map labels that are not people to "".
4. **argument_merges**: groups of argument names that are really the same
   argument. `keep` is the best existing name, `drop` lists the others. Only
   merge true duplicates; a sub-argument that stands on its own stays separate.
5. **best_for_david**: the 3-5 arguments (use the kept names) most useful for
   strengthening David's own case, strongest first, each with one sentence on why.
6. **debates**: one entry per DEBATE MAP question the video argues (group
   the arguments by `question_id`; include proposed NEW questions). For each,
   give the position the video defends, the rival view and whether an advocate
   actually argued it, the step where the two sides split, David's one-line
   verdict, and the kept argument names under it. Order by importance to the
   video's case.
   Also give `rival_representation` (direct | quoted | paraphrased |
   analyst-added | absent) and `next_needed`: the specific evidence, source,
   clarification or test that would move the question forward.
   **subjects**: one entry per DEBATE MAP subject the video substantially
   develops (skip mention-only topics), with a one or two sentence summary:
   the issue, the source's answer and the central disagreement.
   **coverage**: what was examined and what was left out (ads, off-topic chat).
7. **format**: debate | interview | panel | lecture | monologue | sermon | reaction | documentary.
   **direction**: what the video argues for and against, in one line.
   **opposition**: "described-by-speakers" when no advocate of the rival view
   argues it, "defended-by-advocate" when one does, or "mixed".

Return one JSON object only:

```json
{
  "summary": "",
  "format": "",
  "direction": "",
  "opposition": "",
  "speakers": [{"name": "", "role": "host | guest | debater | clip",
                "religious_position": "", "metaphysical_position": "", "scientific_views": ""}],
  "people_aliases": {"variant": "canonical"},
  "argument_merges": [{"keep": "", "drop": [""]}],
  "debates": [{"question_id": "", "question": "", "position_defended": "", "rival_view": "",
               "rival_advocated": false, "rival_representation": "", "split_point": "",
               "verdict": "", "next_needed": "", "arguments": [""]}],
  "subjects": [{"subject_id": "", "summary": "", "span": "mm:ss-mm:ss",
                "depth": "main-focus | substantial | passing"}],
  "coverage": "",
  "best_for_david": [{"argument": "", "why": ""}],
  "follow_ups": []
}
```
