# context/cold — archived history layer

This directory holds context that is NOT needed on every session but must not be lost:
decisions already made, comparisons already run, bugs already noted. Load a file here
only when you're specifically revisiting the history it covers.

## Contents

| File | What it holds |
|---|---|
| `gap-log.md` | Things no amount of code-reading can tell a future agent |

## Triage rule
If something would belong in a kata note (`*-notes.md`) but that note is already committed
and the information is cross-cutting rather than step-specific, it goes here instead.
