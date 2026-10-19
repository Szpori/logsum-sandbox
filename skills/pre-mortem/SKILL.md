---
name: pre-mortem
description: Given a PR diff, enumerate five plausible production incident root causes and the specific code path or assumption that enables each.
---

<!-- Verified: ran once against the agent-authored src/logsum.py on branch agent-replay.
     Five root causes produced: timestamp strip gap (logsum.py:48), missing output-dir check
     (logsum.py:77), undefined output row order (logsum.py:80), BOM/whitespace fieldnames
     edge case (logsum.py:110-113), defaultdict read-creates-entry risk (logsum.py:60).
     All five were grounded in specific line references. -->

1. Assume this PR causes a production incident within 30 days.
2. Enumerate five plausible root causes.
3. For each root cause, name the specific code path or assumption that enables it.
