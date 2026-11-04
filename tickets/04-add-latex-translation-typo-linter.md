# Ticket 04: Add automated typo and delimiter consistency linter for translation.tex

**Project:** TRANSLATION
**Importance:** 3/10
**State:** opened
**Target Model Tier:** Tier 2 / Tier 3 (Free Cloud / Small LLMs)
**Labels:** user, simple-task, tier2-model, tier3-model, TRANSLATION

## Description
Create `lint_translation.py` in `TRANSLATION/` that inspects `translation.tex`, checks for unmatched dollar signs `$...$`, verifies UTF-8 Cyrillic characters, and flags common OCR/transcription typos.

## Acceptance Criteria
1. Implementation is clean, tested, and self-contained within `TRANSLATION/`.
2. Do not modify files outside `TRANSLATION/`.
3. Verify syntax and tests pass without errors.
