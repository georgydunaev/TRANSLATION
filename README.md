# TRANSLATION -- Mathematical Terminology and LaTeX Integrity Suite

## Overview
`TRANSLATION` maintains formal mathematical translation resources, bilingual and multilingual terminology glossaries, and automated verification tools:
- `translation.tex`: Formal logic and Isabelle to first-order theory translation source document.
- `GLOSSARY.md`: Multilingual terminology glossary covering 85+ core terms across mathematical logic, set theory (ZFC, NBG, Morse-Kelley), type theory, and proof assistants (CakeML, Poly/ML, Isabelle, Coq).
- `glossary.json`: Machine-readable structured terminology database.
- `sort_glossary.py`: Automated tool for alphabetical sorting, deduplication, and synchronization between JSON and Markdown glossaries.
- `lint_translation.py`: Linter checking LaTeX delimiters, environment nesting, UTF-8 integrity, and OCR transcription typos.
- `tests/test_translation.py`: Test suite verifying translation and glossary integrity.

## Usage

### Validate and Sort Glossary
```bash
python3 sort_glossary.py
python3 sort_glossary.py --check
```

### Lint LaTeX and Markdown Sources
```bash
python3 lint_translation.py
python3 lint_translation.py --report-json
```

### Run Verification Test Suite
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
