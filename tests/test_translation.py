#!/usr/bin/env python3
"""Comprehensive verification suite for TRANSLATION.

Validates:
1. translation.tex macro, environment, delimiter, and UTF-8 consistency.
2. GLOSSARY.md structure, column integrity, and alphabetical ordering.
3. glossary.json schema, deduplication, and 1:1 sync with GLOSSARY.md.
4. sort_glossary.py and lint_translation.py functionality and CLI execution.
5. Invariants: zero emojis, no arrows in titles, names, or link text.
"""

import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lint_translation import (
    check_latex_delimiters,
    check_latex_environments,
    lint_latex_file,
    lint_markdown_file,
    scan_for_typos,
    verify_utf8_integrity,
)
from sort_glossary import (
    parse_markdown_table,
    sort_json_glossary,
    sort_markdown_glossary,
    validate_glossary_table,
)


class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.tex_path = os.path.join(ROOT, "translation.tex")
        self.md_path = os.path.join(ROOT, "GLOSSARY.md")
        self.json_path = os.path.join(ROOT, "glossary.json")
        self.sort_script = os.path.join(ROOT, "sort_glossary.py")
        self.lint_script = os.path.join(ROOT, "lint_translation.py")

    def test_translation_tex_exists_and_balanced_environments(self):
        self.assertTrue(os.path.isfile(self.tex_path))
        with open(self.tex_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        self.assertGreater(len(content), 100)
        begins = re.findall(r"\\begin\{([^}]+)\}", content)
        ends = re.findall(r"\\end\{([^}]+)\}", content)
        self.assertEqual(len(begins), len(ends))

        # Check full environment nesting via linter
        env_issues = check_latex_environments(content)
        self.assertEqual(
            env_issues,
            [],
            f"Environment nesting issues found: {env_issues}",
        )

    def test_latex_delimiters_via_linter(self):
        with open(self.tex_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        delim_issues = check_latex_delimiters(content)
        self.assertEqual(
            delim_issues,
            [],
            f"Delimiter balance issues in translation.tex: {delim_issues}",
        )

    def test_latex_utf8_integrity(self):
        utf8_issues = verify_utf8_integrity(self.tex_path)
        self.assertEqual(
            utf8_issues,
            [],
            f"UTF-8 integrity issues in translation.tex: {utf8_issues}",
        )

    def test_latex_typo_scanner_detects_known_ocr_typos(self):
        with open(self.tex_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        typos = scan_for_typos(content)
        self.assertGreaterEqual(
            len(typos),
            5,
            "Linter should detect known OCR and transcription typos in translation.tex",
        )
        found_words = {t["found"].lower() for t in typos}
        self.assertIn("theorey", found_words)
        self.assertIn("alphabeth", found_words)

    def test_markdown_glossary_structure_and_count(self):
        self.assertTrue(os.path.isfile(self.md_path))
        with open(self.md_path, encoding="utf-8") as f:
            content = f.read()
        headers, separator, rows = parse_markdown_table(content)
        self.assertGreaterEqual(len(headers), 3)
        self.assertGreaterEqual(
            len(rows),
            75,
            f"GLOSSARY.md should contain at least 75 mathematical terms, found {len(rows)}",
        )
        # Check column consistency
        for idx, row in enumerate(rows, 1):
            self.assertEqual(
                len(row),
                len(headers),
                f"Row {idx} column count mismatch: expected {len(headers)}, got {len(row)}",
            )

    def test_json_glossary_schema_and_count(self):
        self.assertTrue(os.path.isfile(self.json_path))
        with open(self.json_path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 75)
        required_keys = {"english", "russian", "german", "category", "notes"}
        for item in data:
            self.assertTrue(required_keys.issubset(item.keys()))
            self.assertTrue(item["english"].strip())
            self.assertTrue(item["russian"].strip())

    def test_glossary_no_duplicate_keys(self):
        with open(self.json_path, encoding="utf-8") as f:
            data = json.load(f)
        keys = [item["english"].strip().lower() for item in data]
        self.assertEqual(
            len(keys),
            len(set(keys)),
            "Duplicate terms detected in glossary.json",
        )

        with open(self.md_path, encoding="utf-8") as f:
            content = f.read()
        _, _, rows = parse_markdown_table(content)
        md_keys = [r[0].strip().lower() for r in rows]
        self.assertEqual(
            len(md_keys),
            len(set(md_keys)),
            "Duplicate terms detected in GLOSSARY.md",
        )

    def test_glossary_alphabetical_sorting(self):
        self.assertTrue(
            sort_markdown_glossary(self.md_path, check_only=True),
            "GLOSSARY.md is not sorted alphabetically by English term",
        )
        self.assertTrue(
            sort_json_glossary(self.json_path, check_only=True),
            "glossary.json is not sorted alphabetically by English term",
        )

    def test_glossary_markdown_and_json_synchronization(self):
        with open(self.json_path, encoding="utf-8") as f:
            json_data = json.load(f)
        json_keys = [item["english"].strip().lower() for item in json_data]

        with open(self.md_path, encoding="utf-8") as f:
            content = f.read()
        _, _, rows = parse_markdown_table(content)
        md_keys = [r[0].strip().lower() for r in rows]

        self.assertEqual(
            json_keys,
            md_keys,
            "Terms in GLOSSARY.md and glossary.json must match 1:1 in exact sorted order",
        )

    def test_sort_glossary_cli_check(self):
        res = subprocess.run(
            [sys.executable, self.sort_script, "--check"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(
            res.returncode,
            0,
            f"sort_glossary.py --check failed: {res.stderr}\n{res.stdout}",
        )

    def test_lint_translation_cli_execution(self):
        res = subprocess.run(
            [sys.executable, self.lint_script],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(
            res.returncode,
            0,
            f"lint_translation.py execution failed: {res.stderr}\n{res.stdout}",
        )
        self.assertIn("Status:        PASSED", res.stdout)

    def test_linter_synthetic_error_detection(self):
        # 1. Unclosed environment
        bad_latex = "\\begin{theorem}\nSome statement.\n"
        issues = check_latex_environments(bad_latex)
        self.assertTrue(any(i["type"] == "unclosed_environment" for i in issues))

        # 2. Odd dollar count
        odd_dollars = "Let $x \\in A be an element."
        delim_issues = check_latex_delimiters(odd_dollars)
        self.assertTrue(any(i["type"] == "unmatched_dollar_signs" for i in delim_issues))

    def test_invariants_zero_emojis_and_no_arrows(self):
        # Scan files for emojis and arrows
        files_to_check = [
            self.md_path,
            self.json_path,
            self.sort_script,
            self.lint_script,
        ]
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF]"
        )
        arrow_pattern = re.compile(r"(?:->|<-|&rarr;|&larr;|&darr;|&uarr;|→|←|↓|↑)")

        for path in files_to_check:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIsNone(
                emoji_pattern.search(content),
                f"Forbidden emoji found in {os.path.basename(path)}",
            )
            self.assertIsNone(
                arrow_pattern.search(content),
                f"Forbidden arrow symbol found in {os.path.basename(path)}",
            )


if __name__ == "__main__":
    unittest.main()
