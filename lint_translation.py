#!/usr/bin/env python3
"""LaTeX and Markdown translation integrity, delimiter, and typo linter.

Inspects LaTeX sources (translation.tex) and Markdown glossaries (GLOSSARY.md)
for delimiter balancing, environment nesting, macro consistency, UTF-8 integrity,
and common mathematical transcription and OCR typos.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEX_PATH = os.path.join(ROOT_DIR, "translation.tex")
DEFAULT_MD_PATH = os.path.join(ROOT_DIR, "GLOSSARY.md")

# Known transcription, OCR, and spelling errors in mathematical text
COMMON_TYPOS: Dict[str, str] = {
    "alphabeth": "alphabet",
    "theorey": "theory",
    "reperesents": "represents",
    "guranteed": "guaranteed",
    "apllication": "application",
    "restirctions": "restrictions",
    "restirction": "restriction",
    "henken": "henkin",
    "coinside": "coincide",
    "statemens": "statements",
    "defintion": "definition",
    "substituion": "substitution",
    "subsitution": "substitution",
    "indepedent": "independent",
    "hypotheis": "hypothesis",
}


def strip_latex_comments(line: str):
    """Strip LaTeX comments starting with % (unless escaped as \\%)."""
    result = []
    i = 0
    while i < len(line):
        if line[i] == "%":
            if i > 0 and line[i - 1] == "\\":
                result.append(line[i])
            else:
                break
        else:
            result.append(line[i])
        i += 1
    return "".join(result)


def check_latex_environments(text: str):
    """Verify that \\begin{env} and \\end{env} blocks are properly nested."""
    issues: List[Dict[str, Any]] = []
    stack: List[Tuple[str, int]] = []

    for line_num, raw_line in enumerate(text.splitlines(), start=1):
        line = strip_latex_comments(raw_line)
        pattern = re.compile(r"\\(begin|end)\{([^}]+)\}")
        for match in pattern.finditer(line):
            kind, env = match.group(1), match.group(2)
            if kind == "begin":
                stack.append((env, line_num))
            elif kind == "end":
                if not stack:
                    issues.append({
                        "line": line_num,
                        "type": "unmatched_end_environment",
                        "message": f"Unexpected \\end{{{env}}} with no matching \\begin.",
                        "severity": "error",
                    })
                else:
                    top_env, top_line = stack.pop()
                    if top_env != env:
                        issues.append({
                            "line": line_num,
                            "type": "mismatched_environment",
                            "message": f"Mismatched \\end{{{env}}} at line {line_num} does not match \\begin{{{top_env}}} from line {top_line}.",
                            "severity": "error",
                        })

    while stack:
        env, line_num = stack.pop()
        issues.append({
            "line": line_num,
            "type": "unclosed_environment",
            "message": f"Unclosed \\begin{{{env}}} from line {line_num}.",
            "severity": "error",
        })

    return issues


def check_latex_delimiters(text: str):
    """Check paired delimiters in LaTeX: braces, brackets, and math dollar signs."""
    issues: List[Dict[str, Any]] = []

    lines = [strip_latex_comments(l) for l in text.splitlines()]
    clean_text = "\n".join(lines)

    # In LaTeX, \\ represents a line break, not an escaped backslash.
    # Replace \\ with newline placeholder so \\$ is not confused with \$ (escaped dollar).
    normalized = clean_text.replace("\\\\", "\n")

    # 1. Grouping braces balance (ignoring \{ and \})
    escaped_braces_removed = normalized.replace("\\{", "").replace("\\}", "")
    open_braces = escaped_braces_removed.count("{")
    close_braces = escaped_braces_removed.count("}")
    if open_braces != close_braces:
        issues.append({
            "line": 0,
            "type": "unbalanced_braces",
            "message": f"Unbalanced grouping braces: {open_braces} open versus {close_braces} close.",
            "severity": "error",
        })

    # 2. Math mode dollar signs check
    # Escaped literal dollar signs are single backslash \$
    escaped_dollars = normalized.count("\\$")
    math_dollars = normalized.count("$") - escaped_dollars
    if math_dollars % 2 != 0:
        issues.append({
            "line": 0,
            "type": "unmatched_dollar_signs",
            "message": f"Odd number of unescaped dollar signs ({math_dollars}), indicating unclosed math mode.",
            "severity": "error",
        })

    # 3. Check display math brackets \[ ... \]
    display_open = normalized.count("\\[")
    display_close = normalized.count("\\]")
    if display_open != display_close:
        issues.append({
            "line": 0,
            "type": "unbalanced_display_math",
            "message": f"Unbalanced display math delimiters: {display_open} open versus {display_close} close.",
            "severity": "error",
        })

    # 4. Check inline math parens \( ... \)
    inline_open = normalized.count("\\(")
    inline_close = normalized.count("\\)")
    if inline_open != inline_close:
        issues.append({
            "line": 0,
            "type": "unbalanced_inline_math",
            "message": f"Unbalanced inline math delimiters: {inline_open} open versus {inline_close} close.",
            "severity": "error",
        })

    return issues


def scan_for_typos(text: str):
    """Scan text for common OCR and transcription typos."""
    issues: List[Dict[str, Any]] = []

    for line_num, line in enumerate(text.splitlines(), start=1):
        tokens = re.findall(r"\b[A-Za-z]+\b", line)
        for token in tokens:
            low = token.lower()
            if low in COMMON_TYPOS:
                replacement = COMMON_TYPOS[low]
                if token.isupper():
                    replacement = replacement.upper()
                elif token[0].isupper():
                    replacement = replacement.capitalize()

                issues.append({
                    "line": line_num,
                    "type": "spelling_typo",
                    "found": token,
                    "replacement": replacement,
                    "message": f"Line {line_num}: Typo '{token}' detected. Suggestion: '{replacement}'.",
                    "severity": "warning",
                })

    return issues


def verify_utf8_integrity(file_path: str):
    """Verify that file is valid UTF-8 and contains no replacement characters."""
    issues: List[Dict[str, Any]] = []

    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
    except Exception as exc:
        return [{
            "line": 0,
            "type": "file_read_error",
            "message": f"Could not read {file_path}: {exc}",
            "severity": "error",
        }]

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [{
            "line": 0,
            "type": "utf8_decode_error",
            "message": f"Invalid UTF-8 byte sequence in {file_path}: {exc}",
            "severity": "error",
        }]

    if "\ufffd" in text:
        issues.append({
            "line": 0,
            "type": "replacement_character_found",
            "message": "File contains Unicode replacement character (U+FFFD).",
            "severity": "error",
        })

    return issues


def lint_latex_file(file_path: str, strict: bool = False):
    """Run full lint checks on a LaTeX file.

    Returns:
        (is_passing, list_of_issues)
    """
    if not os.path.isfile(file_path):
        return False, [{
            "line": 0,
            "type": "missing_file",
            "message": f"LaTeX file not found at {file_path}",
            "severity": "error",
        }]

    all_issues: List[Dict[str, Any]] = []

    utf8_issues = verify_utf8_integrity(file_path)
    all_issues.extend(utf8_issues)

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    env_issues = check_latex_environments(content)
    all_issues.extend(env_issues)

    delim_issues = check_latex_delimiters(content)
    all_issues.extend(delim_issues)

    typo_issues = scan_for_typos(content)
    all_issues.extend(typo_issues)

    errors = [i for i in all_issues if i.get("severity") == "error"]

    if strict:
        is_passing = len(all_issues) == 0
    else:
        is_passing = len(errors) == 0

    return is_passing, all_issues


def lint_markdown_file(file_path: str):
    """Verify Markdown table structure and bracket balancing."""
    if not os.path.isfile(file_path):
        return False, [{
            "line": 0,
            "type": "missing_file",
            "message": f"Markdown file not found at {file_path}",
            "severity": "error",
        }]

    all_issues: List[Dict[str, Any]] = []
    utf8_issues = verify_utf8_integrity(file_path)
    all_issues.extend(utf8_issues)

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    expected_cols: Optional[int] = None
    in_table = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not in_table:
                in_table = True
                expected_cols = len(cells)
            else:
                if len(cells) != expected_cols:
                    all_issues.append({
                        "line": idx,
                        "type": "markdown_table_column_mismatch",
                        "message": f"Line {idx}: Row has {len(cells)} columns, expected {expected_cols}.",
                        "severity": "error",
                    })
        else:
            in_table = False

    errors = [i for i in all_issues if i.get("severity") == "error"]
    return len(errors) == 0, all_issues


def main():
    parser = argparse.ArgumentParser(
        description="Lint LaTeX and Markdown documents for translation consistency, delimiters, and typos."
    )
    parser.add_argument(
        "--tex", default=DEFAULT_TEX_PATH, help="Path to LaTeX document"
    )
    parser.add_argument(
        "--md", default=DEFAULT_MD_PATH, help="Path to Markdown glossary"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (such as spelling typos) as fatal errors",
    )
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="Output results in structured JSON format",
    )

    args = parser.parse_args()

    results: Dict[str, Any] = {
        "latex_file": args.tex,
        "markdown_file": args.md,
        "latex_passing": True,
        "markdown_passing": True,
        "issues": [],
    }

    tex_ok, tex_issues = lint_latex_file(args.tex, strict=args.strict)
    results["latex_passing"] = tex_ok
    results["issues"].extend(tex_issues)

    md_ok, md_issues = lint_markdown_file(args.md)
    results["markdown_passing"] = md_ok
    results["issues"].extend(md_issues)

    if args.report_json:
        print(json.dumps(results, indent=2))
        return 0 if (tex_ok and md_ok) else 1

    print("=== TRANSLATION LINTER REPORT ===")
    print(f"LaTeX file:    {args.tex}")
    print(f"Markdown file: {args.md}")
    print(f"Status:        {'PASSED' if (tex_ok and md_ok) else 'FAILED'}")
    print("-" * 50)

    errors = [i for i in results["issues"] if i.get("severity") == "error"]
    warnings = [i for i in results["issues"] if i.get("severity") == "warning"]

    if errors:
        print(f"Errors ({len(errors)}):")
        for err in errors:
            loc = f"Line {err['line']}: " if err["line"] > 0 else ""
            print(f"  [ERROR] {loc}{err['message']}")

    if warnings:
        print(f"Warnings / Typo Suggestions ({len(warnings)}):")
        for warn in warnings:
            loc = f"Line {warn['line']}: " if warn["line"] > 0 else ""
            print(f"  [WARN]  {loc}{warn['message']}")

    if not errors and not warnings:
        print("No errors or warnings found. All checks passed cleanly.")

    return 0 if (tex_ok and md_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
