<!-- Shared output format appended to every lens. Edit here, not in each lens file. -->
## OUTPUT (JSON only, this exact shape)

```json
{
  "headline": "one sentence: what this lens found in this video overall",
  "items": [
    {
      "at": "mm:ss",
      "end": "mm:ss or empty",
      "label": "short name for this moment (max 8 words)",
      "quote": "the exact words from the INPUT, verbatim, max 60 words",
      "why": "1-2 sentences: why this matters under this lens",
      "use": "how David can use it (1 sentence)",
      "score": 1
    }
  ],
  "follow_ups": ["specific next checks, or empty"]
}
```

Rules: `score` is 1-5 (5 = best under this lens). Quotes must be verbatim from the INPUT;
never invent a timestamp. Return at most 12 items, best first. If the lens finds nothing,
return an empty `items` list and say so in `headline`.
