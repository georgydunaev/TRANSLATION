#!/usr/bin/env python3
"""Automated mathematical glossary sorting, deduplication, and validation tool.

Maintains alphabetical order and structural integrity of GLOSSARY.md
and glossary.json within the TRANSLATION repository.
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MD_PATH = os.path.join(ROOT_DIR, "GLOSSARY.md")
DEFAULT_JSON_PATH = os.path.join(ROOT_DIR, "glossary.json")


def clean_cell(cell: str):
    """Trim whitespace and normalize internal spaces in a table cell."""
    return re.sub(r"\s+", " ", cell.strip())


def parse_markdown_table(content: str):
    """Parse Markdown table into header, separator, and data rows.

    Returns:
        (headers, separator_cells, data_rows)
    """
    lines = content.splitlines()
    table_lines: List[str] = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(stripped)
        elif in_table:
            break

    if len(table_lines) < 3:
        raise ValueError("Markdown table must contain a header, separator, and at least one data row.")

    header_line = table_lines[0]
    sep_line = table_lines[1]
    raw_data_lines = table_lines[2:]

    headers = [clean_cell(c) for c in header_line.strip("|").split("|")]
    separator = [clean_cell(c) for c in sep_line.strip("|").split("|")]

    data_rows: List[List[str]] = []
    for raw in raw_data_lines:
        cells = [clean_cell(c) for c in raw.strip("|").split("|")]
        if len(cells) != len(headers):
            raise ValueError(
                f"Row column count mismatch: expected {len(headers)}, got {len(cells)} in row: {raw}"
            )
        data_rows.append(cells)

    return headers, separator, data_rows


def format_markdown_table(headers: List[str], data_rows: List[List[str]]):
    """Format table with consistent spacing and alignment."""
    num_cols = len(headers)
    col_widths = [len(h) for h in headers]

    for row in data_rows:
        for idx, cell in enumerate(row):
            if idx < num_cols:
                col_widths[idx] = max(col_widths[idx], len(cell))

    header_cells = [
        f" {headers[i].ljust(col_widths[i])} " for i in range(num_cols)
    ]
    header_str = "|" + "|".join(header_cells) + "|"

    sep_cells = [
        f" {'-' * max(3, col_widths[i])} " for i in range(num_cols)
    ]
    sep_str = "|" + "|".join(sep_cells) + "|"

    row_strings: List[str] = []
    for row in data_rows:
        cells = [
            f" {row[i].ljust(col_widths[i])} " for i in range(num_cols)
        ]
        row_strings.append("|" + "|".join(cells) + "|")

    return "\n".join([header_str, sep_str] + row_strings)


def deduplicate_rows(data_rows: List[List[str]]):
    """Deduplicate rows by first column (case-insensitive).

    Returns:
        (unique_rows, duplicate_keys)
    """
    seen: Dict[str, List[str]] = {}
    duplicates: List[str] = []

    for row in data_rows:
        if not row:
            continue
        key = row[0].strip().lower()
        if key in seen:
            duplicates.append(row[0].strip())
        else:
            seen[key] = row

    return list(seen.values()), duplicates


def sort_rows(data_rows: List[List[str]]):
    """Sort rows alphabetically by English term (first column)."""
    return sorted(data_rows, key=lambda r: r[0].strip().lower())


def validate_glossary_table(headers: List[str], data_rows: List[List[str]]):
    """Validate glossary table structure and content.

    Returns:
        List of error descriptions (empty if valid).
    """
    errors: List[str] = []
    if len(headers) < 3:
        errors.append(f"Header must contain at least 3 columns, found {len(headers)}.")

    expected_cols = len(headers)
    seen_keys: set = set()

    for idx, row in enumerate(data_rows, start=1):
        if len(row) != expected_cols:
            errors.append(f"Row {idx} has {len(row)} columns, expected {expected_cols}.")
        if not row or not row[0].strip():
            errors.append(f"Row {idx} has empty primary English term.")
            continue
        key = row[0].strip().lower()
        if key in seen_keys:
            errors.append(f"Duplicate term '{row[0].strip()}' at row {idx}.")
        seen_keys.add(key)

    sorted_rows = sort_rows(data_rows)
    if [r[0].strip().lower() for r in data_rows] != [r[0].strip().lower() for r in sorted_rows]:
        errors.append("Glossary rows are not sorted alphabetically by English term.")

    return errors


def sort_markdown_glossary(md_path: str = DEFAULT_MD_PATH, check_only: bool = False):
    """Sort and validate Markdown glossary file.

    Returns:
        True if valid and sorted, False otherwise.
    """
    if not os.path.isfile(md_path):
        print(f"Error: Markdown file not found at {md_path}", file=sys.stderr)
        return False

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        headers, _, data_rows = parse_markdown_table(content)
    except Exception as exc:
        print(f"Parsing error in {md_path}: {exc}", file=sys.stderr)
        return False

    unique_rows, duplicates = deduplicate_rows(data_rows)
    sorted_rows = sort_rows(unique_rows)

    if check_only:
        errors = validate_glossary_table(headers, data_rows)
        if errors:
            for err in errors:
                print(f"[CHECK FAILED] {err}", file=sys.stderr)
            return False
        return True

    new_table = format_markdown_table(headers, sorted_rows)

    lines = content.splitlines()
    pre_table: List[str] = []
    post_table: List[str] = []
    in_table = False
    table_ended = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
        elif in_table:
            in_table = False
            table_ended = True
            post_table.append(line)
        elif table_ended:
            post_table.append(line)
        else:
            pre_table.append(line)

    new_parts = []
    if pre_table:
        new_parts.append("\n".join(pre_table).rstrip())
    new_parts.append(new_table)
    if post_table:
        new_parts.append("\n".join(post_table).strip())

    new_content = "\n\n".join(p for p in new_parts if p) + "\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def sort_json_glossary(json_path: str = DEFAULT_JSON_PATH, check_only: bool = False):
    """Sort and validate structured JSON glossary."""
    if not os.path.isfile(json_path):
        return True

    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as exc:
            print(f"JSON error in {json_path}: {exc}", file=sys.stderr)
            return False

    if not isinstance(data, list):
        print(f"JSON root must be a list in {json_path}", file=sys.stderr)
        return False

    seen: Dict[str, dict] = {}
    duplicates: List[str] = []
    for item in data:
        term = item.get("english", "").strip().lower()
        if term in seen:
            duplicates.append(item.get("english", ""))
        else:
            seen[term] = item

    sorted_data = sorted(seen.values(), key=lambda x: x.get("english", "").strip().lower())

    if check_only:
        if duplicates:
            print(f"Duplicate JSON terms found: {duplicates}", file=sys.stderr)
            return False
        if data != sorted_data:
            print("JSON glossary entries are not sorted alphabetically.", file=sys.stderr)
            return False
        return True

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return True


def sync_json_to_markdown(json_path: str = DEFAULT_JSON_PATH, md_path: str = DEFAULT_MD_PATH):
    """Generate or update GLOSSARY.md table directly from glossary.json."""
    if not os.path.isfile(json_path):
        print(f"Error: JSON file not found at {json_path}", file=sys.stderr)
        return False

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_data = sorted(data, key=lambda x: x.get("english", "").strip().lower())

    headers = ["English Term", "Russian Translation", "German Translation", "Notes & Formal Context"]
    data_rows: List[List[str]] = []

    for item in sorted_data:
        data_rows.append([
            item.get("english", "").strip(),
            item.get("russian", "").strip(),
            item.get("german", "").strip(),
            item.get("notes", "").strip(),
        ])

    table_md = format_markdown_table(headers, data_rows)

    doc_lines = [
        "# TRANSLATION Mathematical Terminology Glossary",
        "",
        "Structured bilingual and multilingual terminology reference for formal mathematical logic,",
        "set theory (ZFC, NBG, Morse-Kelley), type theory, and proof assistants (CakeML, Poly/ML, Isabelle, Coq).",
        "",
        f"Total verified terms: {len(data_rows)}.",
        "",
        table_md,
        "",
        "## Usage",
        "To verify or re-sort this table alphabetically, run:",
        "```bash",
        "python3 sort_glossary.py",
        "python3 sort_glossary.py --check",
        "```",
    ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(doc_lines) + "\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Alphabetize, deduplicate, and validate TRANSLATION glossary."
    )
    parser.add_argument(
        "--md", default=DEFAULT_MD_PATH, help="Path to GLOSSARY.md"
    )
    parser.add_argument(
        "--json", default=DEFAULT_JSON_PATH, help="Path to glossary.json"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check sorting without modifying files"
    )
    parser.add_argument(
        "--sync-from-json",
        action="store_true",
        help="Rebuild GLOSSARY.md from glossary.json",
    )

    args = parser.parse_args()

    if args.sync_from_json:
        ok = sync_json_to_markdown(args.json, args.md)
        if not ok:
            return 1
        print("Successfully synchronized GLOSSARY.md from glossary.json.")
        return 0

    md_ok = sort_markdown_glossary(args.md, check_only=args.check)
    json_ok = sort_json_glossary(args.json, check_only=args.check)

    if not (md_ok and json_ok):
        return 1

    if args.check:
        print("All glossary files are alphabetically sorted, valid, and deduplicated.")
    else:
        print("Glossary files processed, deduplicated, and sorted cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
