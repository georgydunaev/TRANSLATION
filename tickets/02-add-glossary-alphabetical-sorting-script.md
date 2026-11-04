# Ticket 02: Add Python script to validate and alphabetize GLOSSARY.md tables

**Project:** TRANSLATION
**Importance:** 3/10
**State:** opened
**Target Model Tier:** Tier 2 / Tier 3 (Free Cloud / Small LLMs)
**Labels:** user, simple-task, tier2-model, tier3-model, TRANSLATION

## Description
Create `sort_glossary.py` in `TRANSLATION/` that parses markdown table rows in `GLOSSARY.md`, verifies 3-column format (English, Russian, Notes), sorts rows alphabetically by English term, and writes back cleanly.

## Acceptance Criteria
1. Implementation is clean, tested, and self-contained within `TRANSLATION/`.
2. Do not modify files outside `TRANSLATION/`.
3. Verify syntax and tests pass without errors.
