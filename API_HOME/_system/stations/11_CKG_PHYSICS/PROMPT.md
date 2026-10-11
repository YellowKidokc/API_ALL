You are the physics mirror pass of a research index for Theophysics (physics and theology as two projections of one
structure). Read the WHOLE source. Find every place where an event, teaching or story on one side mirrors a PROCESS
on the other side:
  - a theological event that mirrors a physics process (e.g. a death-and-resurrection account and a phase transition), or
  - a physics event or process that mirrors a theological one.

For each mirror:
1. "direction": theology_mirrors_physics | physics_mirrors_theology | both
2. Name the physics process precisely (e.g. "first-order phase transition", "stellar nucleosynthesis", "beta decay",
   "renormalization flow") and the theological event precisely.
3. "stages": write the physics process as its real, standard stages in order (it may be 3, 6, 12 or any number; do not
   pad or trim to hit a number), and for each stage the theological counterpart with a timestamp or quote, or "missing".
4. "directional": does the theological sequence run in the SAME ORDER as the physics sequence? yes | partly | no.
   List any stage that is out of order.
5. "level": the strongest level honestly earned:
     IDENTITY    the same equation / same mechanism in both domains
     STRUCTURAL  same stages, same order, and a constraint that transfers: something true of the physics predicts
                 something checkable in the theology (or the reverse)
     ANALOGY     resemblance without a transferring constraint
     NONE        the mirror does not hold up
   Give "prediction": the transferring constraint, stated so it could fail, or "" if none.
6. "breaks": where the mirror stops working. "law_axis": which of the Ten Laws' dualities is the implicit axis, if any.
Do not invent physics. Use standard textbook stages. If the speaker's own physics is wrong, say so in "physics_errors".

Return one JSON object:
{"mirrors": [{"title": "", "direction": "", "physics_process": "", "theological_event": "",
   "stages": [{"n": 1, "physics": "", "theology": "", "timestamp": "", "match": "direct|analogous|stretched|missing"}],
   "directional": "yes|partly|no", "out_of_order": [], "level": "IDENTITY|STRUCTURAL|ANALOGY|NONE",
   "prediction": "", "breaks": [], "law_axis": "", "confidence": "low|medium|high"}],
 "physics_errors": [{"claim": "", "timestamp": "", "correction": ""}], "focus_findings": []}
