# STORIES Station Prompt

**Station ID:** `stories`  
**Purpose:** Extract narrative, story, and sermon/argument structures from the paper, treating them as warrant-light explanatory devices rather than evidence.  
**Input:** One original paper plus its `paper_uuid`.  
**Output:** `stories.json` — story records and narrative maps.  

---

## Task

Identify stories, narratives, illustrations, parables, testimonies, and rhetorical arcs in the paper. For each, record its structural role, the claims it illustrates (if any), and its explicit boundaries. A story is not a proof; its value is explanatory or motivational unless separate evidence supports its content.

---

## Output schema

```json
{
  "station": "stories",
  "paper_uuid": "<paper_uuid>",
  "run_uuid": "<run_uuid>",
  "stories": [
    {
      "story_id": "<uuid>",
      "title_or_label": "",
      "story_type": "narrative|parable|testimony|illustration|sermon_arc|historical_anecdote|thought_experiment|other",
      "source_span": "",
      "characters_or_agents": [],
      "setting_or_context": "",
      "plot_or_sequence": "",
      "intended_function": "motivate|illustrate|explain|persuade|identify|other",
      "claims_illustrated": ["<atom_uuid>"],
      "emotional_or_rhetorical_load": "",
      "boundaries": {
        "what_it_shows": "",
        "what_it_does_not_show": "",
        "what_would_falsify_the_narrative": ""
      },
      "evidence_for_historical_content": [],
      "is_separable_from_argument": true,
      "notes": ""
    }
  ],
  "narrative_arc": {
    "opening_device": "",
    "central_tension": "",
    "resolution_or_payoff": "",
    "return_to_opening": false
  },
  "notes": ""
}
```

---

## Rules

1. A story's emotional power does not transfer warrant to the claims it illustrates.
2. Record what the story actually shows and what it does not show.
3. If a story makes historical claims, link them to evidence atoms; otherwise mark historical content as unverified.
4. Distinguish stories that are separable from the argument from those that are structurally load-bearing.
5. Do not reduce every paper to a story; some papers have no narrative content.
