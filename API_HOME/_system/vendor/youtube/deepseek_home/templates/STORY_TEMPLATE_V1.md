# STORY TEMPLATE V1 — companion to CKG ARGUMENT_FIRST_V1

<!-- Profile: STORY_FIRST_V1 · Status: REVIEW_DRAFT · Base record: CKG_ATOM_RECORD_V3.2_UNIFIED.
     Station: `stories`. A story record is an auxiliary record like an argument
     record: it links to CLAIM / EVIDENCE atoms and adds no primary Atom type.
     Python supplies IDs, hashes and counts. AI proposes content and ratings.
     Only a human ruling admits anything. -->

## Story or argument? The decision rule

Read each passage and decide what it is doing:

| The passage... | Record it as | Link |
|---|---|---|
| tells what happened, to inspire, illustrate or teach | **story** | none |
| gives reasons for a conclusion | **argument** | none |
| tells what happened **and offers it as evidence** for a conclusion ("my healing shows God is real") | **story**, once | the argument cites `story: <title>` as evidence; the story names the argument in `used_as_evidence_for` |
| states a moral at the end of a narrative | **story** (the moral is its `lesson`) | none; a moral alone is not an argument |

One passage is one record. Never count the same passage as both a story and a separate argument.

## Story record

**Identity:** {{story ID}} · **Title:** {{short memorable title}} · **Source:** {{video / book / page}} · **Span:** {{start–end}}

**Story type:** {{personal-testimony / reported-testimony / biblical-narrative / historical / illustration / parable / hypothetical}}
**Teller:** {{who tells it}} · **Subject of the story:** {{whom it happened to}} · **Relation:** {{first-hand / second-hand / further removed}}

### What happened
{{Two to four plain sentences.}}

| Setup | Conflict | Turning point | Outcome |
|---|---|---|---|
| {{situation}} | {{problem or stakes}} | {{the moment things change}} | {{how it ends}} |

### What the teller does with it
- **Intended lesson (in the teller's terms):** {{ }}
- **Presented as:** {{one person's experience / a general promise to others / an illustration}}
- **Offered as evidence for:** {{argument ID and name, or "told for its own sake"}}
- **Scripture tied to it:** {{references}}
- **Themes:** {{kebab-case tags: forgiveness, provision, conversion...}}

### Evidence status — separate from how well it is told
History chain (fill what the source gives; leave the rest UNKNOWN):
event → observers → witness → testimony → transmission → this telling

- **Status:** {{unverified / sourced-in-video / publicly-verifiable / verified (human only)}}
- **What would corroborate it:** {{records, named people, dates, documents}}
- **Caution:** {{anything a skeptic would reasonably question}}

### How well it is told — AI proposal
Anchors: **1 weak · 3 usable · 5 especially strong**, for a general Christian audience. Each score needs a reason. Leave unassessed scales blank; never fill with a default.

| Scale | Score | Reason |
|---|---|---|
| Clarity: can someone follow what happened? | {{1-5}} | {{ }} |
| Emotional impact: are the stakes and human experience felt? | {{1-5}} | {{ }} |
| Memorability: is there a detail, contrast or turning point people will remember? | {{1-5}} | {{ }} |
| Teaching value: does it carry a clear, relevant lesson? | {{1-5}} | {{ }} |
| Retelling usefulness: could David use it in conversation, an article, a sermon or a short video? | {{1-5}} | {{ }} |

### David's rating
{{blank until David rates it; never pre-filled by AI}}

### Useful for
{{the conversations, topics or pieces where this story would work}}

**Admission:** candidate · human ruling pending
