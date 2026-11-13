# Ticket 04: Add automated typo and delimiter consistency linter for translation.tex

**Project:** TRANSLATION
**Importance:** 3/10
**State:** closed
**Target Model Tier:** Tier 2 / Tier 3 (Free Cloud / Small LLMs)
**Labels:** user, simple-task, tier2-model, tier3-model, TRANSLATION

## Description
Create `lint_translation.py` in `TRANSLATION/` that inspects `translation.tex`, checks for unmatched dollar signs `$...$`, verifies UTF-8 Cyrillic characters, and flags common OCR/transcription typos.

## Acceptance Criteria
1. Implementation is clean, tested, and self-contained within `TRANSLATION/`.
2. Do not modify files outside `TRANSLATION/`.
3. Verify syntax and tests pass without errors.

## Resolution
Resolved. Created `lint_translation.py` providing:
- LaTeX environment balancing check (`\begin{env} ... \end{env}`) with stack nesting verification.
- Delimiter integrity verification for inline and display math dollar signs, grouping braces, and display/inline brackets.
- UTF-8 file integrity check and Cyrillic character support validation.
- OCR and transcription typo scanner identifying known typos (theorey to theory, Alphabeth to Alphabet, Henken to Henkin, apllication to application, etc.) with line numbers and suggestions.
- Markdown table column consistency validation.
- Structured JSON and human-readable reporting modes.
- Verified in `tests/test_translation.py`.
