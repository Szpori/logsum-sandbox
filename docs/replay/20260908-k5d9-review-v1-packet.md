Sensitivity: internal

# Replay packet — K 5.D.9 review attempt v1

**Run ID:** `20260908-k5d9-review-v1`  
**Kata:** K 5.D.9 — Seven-lens adversarial code review  
**Outcome:** Failed — reviewed wrong artefact; output discarded, not committed  
**Date reconstructed:** 2026-10-19  

---

## 1. Task / prompt

Perform a seven-lens adversarial code review of the `--format {csv,json}` flag
implementation on branch `format-flag-T1`.

The review session was given these instructions:
- Primary artefact: the implementation diff for the `--format` flag (changes to `src/logsum.py`)
- Read-only context: `tests/test_format_flag_independent.py`, `tests/test_logsum.py`
- Spec: `specs/format-flag/spec.md` (signed off 2026-08-30)
- Framework: seven-lens review (Behaviour Preservation, Hidden Assumptions, Spec/ADR Drift,
  Independent Tests Check, Edge Cases, Security/Tool-Call Surface, Over-engineering)
- Output format: findings table per lens, summary table F1–Fn, final verdict

---

## 2. Context snapshot

| Item | Provided | Notes |
|------|----------|-------|
| Implementation diff (`src/logsum.py`) | Yes — pasted as text | Primary review target |
| Spec (`specs/format-flag/spec.md`) | Yes — pasted as text | |
| Independent tests (`tests/test_format_flag_independent.py`) | Yes — pasted as text | Intended as read-only context |
| Existing tests (`tests/test_logsum.py`) | Yes — pasted as text | |
| Session isolation | Tier A — fresh session, no prior context | |
| Seven-lens framework definition | Not explicitly re-stated in prompt | **Gap — framework was referenced by name but lens definitions were not pasted** |

---

## 3. Ordered action log

*(Reconstructed from conversation record — exact internal steps not recoverable)*

1. Session received four text blocks: diff, spec, independent tests, existing tests
2. Session identified the largest and most structurally complex artefact in the context window
3. Session selected `tests/test_format_flag_independent.py` as the primary review target
   rather than the diff of `src/logsum.py`
4. Session applied a review framework with custom lens names (not the seven-lens framework)
5. Session produced a verdict: findings about test coverage, isolation, and structure
6. Session delivered output with header: **`Artefact reviewed: tests/test_format_flag_independent.py`**
7. Human read the header and identified the wrong-artefact failure
8. Session output was discarded; review was re-run with explicit artefact instruction

---

## 4. Output — offending portion

*(Partial reconstruction from conversation record — full session output not preserved in repo)*

```
# Review — format-flag branch (T1)
**Artefact reviewed:** `tests/test_format_flag_independent.py`
**Context (read-only):** `src/logsum.py` diff, `specs/format-flag/spec.md`

## Verdict: APPROVE

The independent test suite is well-structured and covers the six acceptance
criteria from the spec. Isolation is maintained — no internal imports. Test
helpers are reusable across classes.

### Coverage lens
...

### Isolation lens
...

### Boundary lens
...
```

**What was wrong:**
- Artefact under review: `tests/test_format_flag_independent.py` ← should be `src/logsum.py`
- Lens names: `Coverage`, `Isolation`, `Boundary` ← should be the seven named lenses
- The tests were treated as the primary artefact and the implementation diff as context,
  reversing the intended relationship

**What was accidentally correct:**
- The verdict (APPROVE) was directionally right — the implementation is spec-compliant
- Several observations about test coverage were valid, just applied to the wrong question

---

## 5. Triage note

**Failure mode:** Artefact misidentification — session selected the wrong primary target

**Trigger:** The four-item context bundle (diff, spec, independent tests, existing tests)
was provided without explicit primacy signalling. `tests/test_format_flag_independent.py`
is the largest single file in the bundle (~600 lines vs. ~170 for the diff). In the
absence of an unambiguous "review THIS" directive, the session gravitised toward the
largest, most structurally rich artefact.

A secondary contributor: the seven-lens framework was referenced by name ("seven-lens
adversarial review") but the lens definitions were not pasted into the prompt. Without
the canonical lens list, the session substituted plausible-sounding lens names derived
from the artefact it had chosen (tests → Coverage, Isolation, Boundary).

**How it was caught:** The `Artefact reviewed:` header at the top of the output.
The failure was visible immediately on first read, before any findings were considered.

**Correction applied:**
1. Session output discarded entirely
2. Re-run with explicit directive: "Review `src/logsum.py` (the diff). The tests are
   read-only context."
3. Seven-lens definitions pasted into the corrected prompt
4. Corrected output committed as `cbcbed2 add review`

**Root cause (one line):** Prompt did not unambiguously name the primary artefact;
session defaulted to the largest file.

---

## 6. Prevention

| Signal | Prevention |
|--------|------------|
| Multiple artefacts in context | Always open the prompt with `"Review <specific-file>."` — not a task description that the session must interpret |
| Framework referenced by name only | Paste the lens list inline or link to a definition the session can read; names alone are not definitions |
| Wrong-artefact failure | Read the `Artefact reviewed:` header before reading any findings — it is a fast reject signal |

---

## 7. Redactions applied

- None

---

## 8. Model and client metadata

| Field | Value |
|-------|-------|
| Client | Claude Code (CLI) |
| Model / version | claude-sonnet-4-6 |
| Date / time | 2026-09-08 (approximate — exact timestamp not recoverable; session output was discarded before commit) |
| Mode | Supervised — human reviewed output immediately after delivery |
| Isolation | Tier A — fresh session with no prior conversation context |
| Limitation | This packet is a reconstruction. The failed session's full output was not persisted to disk or committed to the repo; the offending header and lens names are recovered from the conversation record of the supervising session, not from the original session transcript. |
