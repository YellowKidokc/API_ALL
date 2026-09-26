# TASK: map a video's arguments onto the DEBATE MAP

The INPUT is a YouTube transcript, or one chunk of it, with [mm:ss] timestamps.

**Purpose: David mines these videos to develop his own arguments.** He needs to
see, for each question in dispute, exactly which step of an argument a speaker
defends, who disputes that step, and what evidence and sources are in play.
Be a demanding sparring partner: rate a popular but weak argument as weak and
give the better version if one exists.

## What to extract
- **Every argument**: any attempt to persuade, whether a reason for a
  conclusion, an objection, a rebuttal, an appeal to evidence or authority, or
  a testimony offered as evidence. Include weak ones and the objections the
  speakers answer. Do not merge distinct arguments; list a recurring argument
  once with each passage's timestamp.
- **Break each argument into linked steps.** "A beginning throws out
  materialism" is several claims: reality had an absolute beginning → a
  beginning needs a cause → the cause is not physical → so physical reality is
  not all there is. Number the steps so David can see which step someone
  accepts or disputes.
- **Keep three things apart**:
  - the position a speaker *defends*
  - an opposing position *as the speaker describes it* (a straw man is possible)
  - an opposing position *actually argued by its advocate* in the video
- **Keep worldview separate from position.** "Christian", "materialist" and
  "accepts evolution" are not mutually exclusive teams. Record each speaker's
  religious, metaphysical and scientific positions separately.
- **Resources**: every book, paper, study, person or video a speaker cites,
  with how it was spoken, your identification, the timestamp, and the claim
  it supposedly supports. `verified` is always false; a person checks later.
- **People, places, things, scripture.** Auto-captions garble names: give your
  correction plus `as_heard` when it differs.

- **Exchanges**: every objection that actually occurs in the source, in order,
  with the reply. Mode is DIRECT when an opposing speaker raises it, REPORTED
  when a speaker relays what a critic said, and SELF_POSED when a speaker
  raises an objection to their own view. Your own `strongest_objection` is
  not an exchange.
- A topic label or bare assertion is not an argument. Keep brief or incomplete
  arguments with `complete: false`; do not invent premises to fill them.

- **Story or argument? Decide for every passage.** Many passages are stories,
  not arguments.
  - A narrative told for its own sake, to inspire, or to illustrate a point
    is a **story**. Record it only in `stories`.
  - Reasons offered for a conclusion form an **argument**. Record it only in
    `arguments`.
  - A story **offered as evidence** for a conclusion (for example, "my
    conversion shows God is real" or "this healing proves...") is recorded
    once, in `stories`, with `used_as_evidence_for` naming the argument. The
    argument lists "story: <title>" in `evidence_cited`. Never record the
    same passage as two separate items.
  - A narrative is not an argument just because it has a moral.
- **Segments**: label each stretch of the input as story, bible-teaching,
  theology, argument, application or other. One stretch can carry one label;
  split where the mode changes.
- **Stories and testimonies** are first-class, not just evidence for
  arguments. Rate how well each is *told* on five 1-5 scales (1 weak, 3
  usable, 5 especially strong, for a general Christian audience), each with a
  short reason: clarity, emotional_impact, memorability, teaching_value,
  retelling_usefulness. Storytelling quality and factual support are separate:
  a gripping story can be unverified. Record whether the speaker presents it
  as one person's experience or as a promise for others.
- **Bible teaching**: every passage quoted, explained or mentioned, and for
  real teaching segments rate clarity, attention to passage context and
  practical usefulness (1-5 with reasons) and name the interpretive approach.
- **Theological concepts** (grace, salvation, providence, Trinity...) with the
  particular interpretation presented, and **practical lessons**: what the
  speaker urges the listener to believe or do, and what supports it.

Skip sponsor reads and ads entirely. `timestamps` gives where each distinct
passage starts, at most 4. `topics` are subjects, never people.

## Classification
- `question_id`: the one DEBATE MAP question the argument answers. If none
  fits, use `NEW` and add an entry to `new_questions`.
- `family`: the argument's type, as `family` or `family/subtype`:
  resurrection (minimal-facts, empty-tomb, appearances, early-creed,
  alternative-theories) · historical-jesus · bible-reliability · prophecy ·
  miracles · cosmological (kalam, contingency, leibniz) · fine-tuning · design
  (origin-of-life, irreducible-complexity, information) · evolution · moral ·
  consciousness · reason (eaan) · naturalism · problem-of-evil · hiddenness ·
  religious-experience · testimony · comparative-religion · spiritual-warfare ·
  eschatology · culture-society · methodology · other
- `version`: the specific form, e.g. "Kalam using modern cosmology" or
  "Plantinga's EAAN".

## Output
Return **one JSON object only**. All keys are required; use [] or "" when empty.

```json
{
  "summary": "3-5 sentences",
  "speakers": [{"name": "", "as_heard": "", "role": "host | guest | debater | clip",
                "religious_position": "", "metaphysical_position": "", "scientific_views": ""}],
  "arguments": [{
    "name": "short memorable name",
    "question_id": "Q-BEGIN-ABSOLUTE",
    "family": "cosmological/kalam",
    "version": "",
    "stance": "for-christianity | against-christianity | for-theism | against-theism | neutral | other",
    "speaker": "",
    "timestamps": ["mm:ss"],
    "steps": [{"n": 1, "claim": "", "role": "premise | evidence | inference | conclusion",
               "disputed_by": "who or what position rejects this step, or empty"}],
    "conclusion": "",
    "plain": "The source argues that [conclusion] because [main reasons]. Its crucial step is [step].",
    "provenance": "established | adaptation | original | unknown",
    "attributed_to": "who the standard formulation is usually credited to (e.g. William Lane Craig, Alvin Plantinga), or empty; 'original' means the speaker's own framing, not a proven first",
    "complete": true,
    "hidden_premises": ["unstated premises the argument needs"],
    "opposing_as_described": "the rival view as this speaker presents it, or empty",
    "opposing_advocated_in_video": false,
    "competing_positions": ["named rival positions or models on this question"],
    "evidence_cited": ["studies, numbers, experts, events used as support"],
    "quote": {"text": "verbatim, max 25 words", "at": "mm:ss"},
    "support": "demonstrated-formal | demonstrated-empirical | defensible | asserted | unclear",
    "falsifiable": "yes | no | not-assessed",
    "confidence": "low | medium | high",
    "strength": "strong | moderate | weak",
    "strongest_objection": "",
    "objection_answered": "",
    "what_survives": "narrowest defensible version after the strongest objection",
    "not_established": "nearby claims this does NOT earn",
    "use_for_david": "how to reuse or strengthen it; the better version if weak",
    "checks": {"formal": "what a Lean/logic check could establish, or empty",
               "empirical": "literature or data that would confirm or break it",
               "adversarial": "the counterexample to test against"},
    "research_queries": ["search queries to find the primary formulation and the best opposing one; never invent a citation"],
    "tags": ["kebab-case"]
  }],
  "exchanges": [{"target_argument": "argument name", "objection": "", "objection_by": "",
                 "objection_at": "mm:ss", "mode": "DIRECT | REPORTED | SELF_POSED",
                 "reply": "or NO_REPLY_IN_SOURCE", "reply_at": "mm:ss", "follow_up": "or NONE_IN_SOURCE",
                 "coverage": "ADDRESSED | PARTLY_ADDRESSED | NOT_ADDRESSED"}],
  "resources": [{"spoken_as": "", "identified_as": "", "author": "", "kind": "book | paper | study | video | person | other",
                 "at": "mm:ss", "supports": "claim it was cited for", "cited_by_speaker": true, "verified": false}],
  "claims_to_verify": [{"claim": "", "at": "mm:ss", "why": ""}],
  "new_questions": [{"subject_id": "S-...", "question": ""}],
  "people": [{"name": "", "as_heard": "", "role": "", "present": true}],
  "places": [{"name": "", "context": ""}],
  "things": [{"name": "", "kind": "organization | work | event | experiment | artifact | concept | other", "context": ""}],
  "segments": [{"start": "mm:ss", "end": "mm:ss", "kind": "story | bible-teaching | theology | argument | application | other", "label": ""}],
  "stories": [{"title": "", "story_type": "personal-testimony | reported-testimony | biblical-narrative | historical | illustration | parable | hypothetical",
               "teller": "", "start": "mm:ss", "end": "mm:ss", "summary": "", "people": [""],
               "conflict": "", "turning_point": "", "outcome": "", "lesson": "the speaker's intended lesson, in their terms",
               "presented_as": "one-person-experience | general-promise | illustration",
               "evidence_status": "unverified | sourced-in-video | publicly-verifiable",
               "themes": ["kebab-case"], "scripture": [""], "useful_for": "",
               "used_as_evidence_for": "argument name, or empty if told for its own sake",
               "ratings": {"clarity": {"score": 3, "reason": ""}, "emotional_impact": {"score": 3, "reason": ""},
                           "memorability": {"score": 3, "reason": ""}, "teaching_value": {"score": 3, "reason": ""},
                           "retelling_usefulness": {"score": 3, "reason": ""}}}],
  "scripture": [{"ref": "Romans 8:28", "mode": "quoted | explained | mentioned", "speaker": "", "at": "mm:ss",
                 "context": "what it was used for"}],
  "teaching": [{"topic": "passage or doctrine taught", "speaker": "", "start": "mm:ss", "end": "mm:ss",
                "approach": "e.g. historical-grammatical, devotional, typological, proof-text",
                "summary": "", "ratings": {"clarity": {"score": 3, "reason": ""},
                                          "context_attention": {"score": 3, "reason": ""},
                                          "practical_usefulness": {"score": 3, "reason": ""}}}],
  "concepts": [{"concept": "grace", "interpretation": "the particular view presented", "speaker": "", "at": "mm:ss"}],
  "lessons": [{"lesson": "what the listener is urged to believe or do", "supported_by": "story, passage or argument", "at": "mm:ss"}],
  "topics": [],
  "theophysics_tags": ["only from: physics theology information consciousness morality mathematics, var-G var-M var-E var-S var-T var-K var-R var-Q var-F var-C, law-01 to law-10"],
  "follow_ups": []
}
```
