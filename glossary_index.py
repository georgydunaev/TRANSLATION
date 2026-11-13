#!/usr/bin/env python3
"""Indexed terminology dictionary with fuzzy matching and bidirectional lookup.

Provides an indexed hash structure for formal mathematical terminology across
English, Russian, and German, supporting case-insensitive normalization,
fuzzy matching, bidirectional translation, and glossary consistency validation.
"""

import argparse
from dataclasses import asdict, dataclass
import difflib
import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON_PATH = os.path.join(ROOT_DIR, "glossary.json")
DEFAULT_MD_PATH = os.path.join(ROOT_DIR, "GLOSSARY.md")

VALID_CATEGORIES: Set[str] = {
    "mathematical_logic",
    "set_theory",
    "class_theory",
    "proof_theory",
    "type_theory",
    "proof_assistants",
    "foundations",
    "category_theory",
    "model_theory",
    "general",
}


def normalize_term(term: str):
    """Normalize a mathematical term for case-insensitive and robust matching.

    Strips leading and trailing punctuation, normalizes Unicode NFKC,
    collapses whitespace, and converts to lowercase.
    """
    if not term:
        return ""

    # Normalize Unicode characters
    normalized = unicodedata.normalize("NFKC", term.strip())

    # Lowercase
    normalized = normalized.lower()

    # Map Russian 'ё' to 'е' for search tolerance
    normalized = normalized.replace("ё", "е")

    # Collapse multiple whitespace
    normalized = re.sub(r"\s+", " ", normalized)

    # Trim enclosing quotes or markdown formatting
    normalized = normalized.strip(" \t\n\r`\"'*_")

    return normalized


def extract_aliases(term: str):
    """Extract primary term and parenthetical aliases.

    Example:
        'Arity (Valence)' yields ['arity (valence)', 'arity', 'valence']
        'Арность (местность)' yields ['арность (местность)', 'арность', 'местность']
    """
    aliases: List[str] = []
    norm = normalize_term(term)
    if not norm:
        return aliases

    aliases.append(norm)

    # Match patterns like 'term (alias)' or 'term / alias'
    paren_match = re.match(r"^([^(]+)\s*\(([^)]+)\)\s*$", norm)
    if paren_match:
        primary = normalize_term(paren_match.group(1))
        alt = normalize_term(paren_match.group(2))
        if primary and primary not in aliases:
            aliases.append(primary)
        if alt and alt not in aliases:
            aliases.append(alt)

    slash_parts = [normalize_term(p) for p in norm.split("/")]
    if len(slash_parts) > 1:
        for p in slash_parts:
            if p and p not in aliases:
                aliases.append(p)

    return aliases


@dataclass
class GlossaryEntry:
    """A structured mathematical glossary entry across multiple languages."""

    english: str
    russian: str
    german: str
    category: str
    notes: str
    entry_id: int = 0

    def get_translation(self, lang: str):
        """Retrieve translation by language code or name."""
        l = lang.lower().strip()
        if l in ("en", "english"):
            return self.english
        elif l in ("ru", "russian"):
            return self.russian
        elif l in ("de", "german", "deutsch"):
            return self.german
        raise ValueError(f"Unsupported language: {lang}")

    def to_dict(self):
        """Convert entry to standard dictionary."""
        return asdict(self)


class TerminologyIndex:
    """Indexed hash dictionary for fast bilingual and multilingual terminology lookup."""

    def __init__(self, entries: Optional[List[Dict[str, Any]]] = None):
        self._entries: List[GlossaryEntry] = []
        self._index_en: Dict[str, GlossaryEntry] = {}
        self._index_ru: Dict[str, GlossaryEntry] = {}
        self._index_de: Dict[str, GlossaryEntry] = {}
        self._index_aliases: Dict[str, List[GlossaryEntry]] = {}
        self._by_category: Dict[str, List[GlossaryEntry]] = {}

        if entries:
            self.load_entries(entries)

    def load_entries(self, entries: List[Dict[str, Any]]):
        """Build indexed hash structures from a list of entry dictionaries."""
        self._entries.clear()
        self._index_en.clear()
        self._index_ru.clear()
        self._index_de.clear()
        self._index_aliases.clear()
        self._by_category.clear()

        for idx, item in enumerate(entries, start=1):
            entry = GlossaryEntry(
                english=item.get("english", "").strip(),
                russian=item.get("russian", "").strip(),
                german=item.get("german", "").strip(),
                category=item.get("category", "").strip(),
                notes=item.get("notes", "").strip(),
                entry_id=idx,
            )
            self._entries.append(entry)

            # English index and aliases
            for alias in extract_aliases(entry.english):
                self._index_en.setdefault(alias, entry)
                self._index_aliases.setdefault(alias, []).append(entry)

            # Russian index and aliases
            for alias in extract_aliases(entry.russian):
                self._index_ru.setdefault(alias, entry)
                self._index_aliases.setdefault(alias, []).append(entry)

            # German index and aliases
            for alias in extract_aliases(entry.german):
                self._index_de.setdefault(alias, entry)
                self._index_aliases.setdefault(alias, []).append(entry)

            # Category index
            cat = entry.category or "general"
            self._by_category.setdefault(cat, []).append(entry)

    @classmethod
    def from_json_file(cls, json_path: str = DEFAULT_JSON_PATH):
        """Instantiate index directly from glossary.json."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def __len__(self):
        return len(self._entries)

    def all_entries(self):
        """Return list of all glossary entries."""
        return list(self._entries)

    def lookup(
        self,
        term: str,
        source_lang: str = "any",
    ):
        """Perform exact case-insensitive normalized lookup in O(1) time.

        Args:
            term: The search term.
            source_lang: 'en', 'ru', 'de', or 'any'.
        """
        norm = normalize_term(term)
        if not norm:
            return None

        lang = source_lang.lower().strip()

        if lang in ("en", "english"):
            return self._index_en.get(norm)
        elif lang in ("ru", "russian"):
            return self._index_ru.get(norm)
        elif lang in ("de", "german", "deutsch"):
            return self._index_de.get(norm)
        elif lang == "any":
            if norm in self._index_en:
                return self._index_en[norm]
            if norm in self._index_ru:
                return self._index_ru[norm]
            if norm in self._index_de:
                return self._index_de[norm]
            matches = self._index_aliases.get(norm)
            if matches:
                return matches[0]

        return None

    def translate(
        self,
        term: str,
        source_lang: str,
        target_lang: str,
    ):
        """Synchronized bidirectional translation between English, Russian, and German."""
        entry = self.lookup(term, source_lang=source_lang)
        if entry is None:
            # Fall back to fuzzy lookup if exact match not found
            fuzzy_results = self.fuzzy_lookup(term, source_lang=source_lang, max_results=1, cutoff=0.85)
            if fuzzy_results:
                entry = fuzzy_results[0][0]

        if entry is None:
            return None

        return entry.get_translation(target_lang)

    def fuzzy_lookup(
        self,
        query: str,
        source_lang: str = "any",
        max_results: int = 5,
        cutoff: float = 0.6,
    ):
        """Perform fuzzy matching using sequence similarity and token overlap.

        Returns:
            List of tuples: (entry, similarity_score, matched_term)
            sorted by score in descending order.
        """
        norm_query = normalize_term(query)
        if not norm_query:
            return []

        lang = source_lang.lower().strip()
        candidates: List[Tuple[str, GlossaryEntry]] = []

        if lang in ("en", "english"):
            candidates = list(self._index_en.items())
        elif lang in ("ru", "russian"):
            candidates = list(self._index_ru.items())
        elif lang in ("de", "german", "deutsch"):
            candidates = list(self._index_de.items())
        else:
            candidates.extend(self._index_en.items())
            candidates.extend(self._index_ru.items())
            candidates.extend(self._index_de.items())

        scored: List[Tuple[GlossaryEntry, float, str]] = []
        seen_entries: Set[int] = set()

        for candidate_term, entry in candidates:
            if entry.entry_id in seen_entries:
                continue

            # Compute sequence ratio
            seq_ratio = difflib.SequenceMatcher(None, norm_query, candidate_term).ratio()

            # Word token Jaccard similarity bonus for multi-word mathematical terms
            q_words = set(norm_query.split())
            c_words = set(candidate_term.split())
            if q_words and c_words:
                jaccard = len(q_words & c_words) / len(q_words | c_words)
            else:
                jaccard = 0.0

            # Substring / prefix bonus
            substring_bonus = 0.0
            if norm_query in candidate_term or candidate_term in norm_query:
                substring_bonus = 0.15

            final_score = min(1.0, max(seq_ratio, (seq_ratio * 0.7 + jaccard * 0.3)) + substring_bonus)

            if final_score >= cutoff:
                scored.append((entry, round(final_score, 4), candidate_term))
                seen_entries.add(entry.entry_id)

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:max_results]

    def validate_consistency(self):
        """Validate consistency, completeness, and bidirectional integrity of the glossary."""
        errors: List[str] = []
        warnings: List[str] = []

        seen_en: Dict[str, int] = {}
        seen_ru: Dict[str, int] = {}
        seen_de: Dict[str, int] = {}

        for idx, entry in enumerate(self._entries, start=1):
            # Check completeness
            if not entry.english:
                errors.append(f"Entry {idx}: Missing English term.")
            if not entry.russian:
                errors.append(f"Entry {idx}: Missing Russian translation for '{entry.english}'.")
            if not entry.german:
                errors.append(f"Entry {idx}: Missing German translation for '{entry.english}'.")

            # Check category validity
            if entry.category and entry.category not in VALID_CATEGORIES:
                warnings.append(
                    f"Entry {idx} ('{entry.english}'): Unknown category '{entry.category}'."
                )

            # Check duplicate primary terms
            norm_en = normalize_term(entry.english)
            if norm_en in seen_en:
                errors.append(
                    f"Duplicate English term '{entry.english}' at entry {idx} (first seen at entry {seen_en[norm_en]})."
                )
            else:
                seen_en[norm_en] = idx

            norm_ru = normalize_term(entry.russian)
            if norm_ru:
                if norm_ru in seen_ru:
                    warnings.append(
                        f"Shared Russian translation '{entry.russian}' at entry {idx} and entry {seen_ru[norm_ru]}."
                    )
                else:
                    seen_ru[norm_ru] = idx

            norm_de = normalize_term(entry.german)
            if norm_de:
                if norm_de in seen_de:
                    warnings.append(
                        f"Shared German translation '{entry.german}' at entry {idx} and entry {seen_de[norm_de]}."
                    )
                else:
                    seen_de[norm_de] = idx

            # Bidirectional consistency check:
            # Look up Russian translation; ensure it maps back to this entry
            ru_lookup = self.lookup(entry.russian, source_lang="ru")
            if ru_lookup is None:
                errors.append(
                    f"Entry {idx}: Russian term '{entry.russian}' does not index back to entry."
                )

            de_lookup = self.lookup(entry.german, source_lang="de")
            if de_lookup is None:
                errors.append(
                    f"Entry {idx}: German term '{entry.german}' does not index back to entry."
                )

        return {
            "is_valid": len(errors) == 0,
            "total_entries": len(self._entries),
            "errors": errors,
            "warnings": warnings,
        }


def validate_glossary_consistency(json_path: str = DEFAULT_JSON_PATH):
    """Inspect and validate glossary consistency directly from JSON file."""
    if not os.path.isfile(json_path):
        return {
            "is_valid": False,
            "total_entries": 0,
            "errors": [f"File not found: {json_path}"],
            "warnings": [],
        }

    index = TerminologyIndex.from_json_file(json_path)
    return index.validate_consistency()


def main():
    parser = argparse.ArgumentParser(
        description="Bilingual and Multilingual Mathematical Terminology Index"
    )
    parser.add_argument("--json", default=DEFAULT_JSON_PATH, help="Path to glossary.json")
    parser.add_argument("--lookup", help="Perform exact lookup for term")
    parser.add_argument("--fuzzy", help="Perform fuzzy matching for term")
    parser.add_argument("--lang", default="any", help="Source language (en, ru, de, any)")
    parser.add_argument("--translate-to", help="Target translation language (en, ru, de)")
    parser.add_argument("--validate", action="store_true", help="Run glossary consistency check")

    args = parser.parse_args()

    if not os.path.isfile(args.json):
        print(f"Error: glossary file not found: {args.json}", file=sys.stderr)
        return 1

    index = TerminologyIndex.from_json_file(args.json)

    if args.validate:
        report = index.validate_consistency()
        print(f"Glossary Entries: {report['total_entries']}")
        print(f"Consistency:      {'PASSED' if report['is_valid'] else 'FAILED'}")
        if report["errors"]:
            print(f"Errors ({len(report['errors'])}):")
            for err in report["errors"]:
                print(f"  [ERROR] {err}")
        if report["warnings"]:
            print(f"Warnings ({len(report['warnings'])}):")
            for warn in report["warnings"]:
                print(f"  [WARN]  {warn}")
        return 0 if report["is_valid"] else 1

    if args.lookup:
        entry = index.lookup(args.lookup, source_lang=args.lang)
        if entry:
            if args.translate_to:
                print(entry.get_translation(args.translate_to))
            else:
                print(f"English:  {entry.english}")
                print(f"Russian:  {entry.russian}")
                print(f"German:   {entry.german}")
                print(f"Category: {entry.category}")
                print(f"Notes:    {entry.notes}")
            return 0
        else:
            print(f"Term '{args.lookup}' not found.")
            return 1

    if args.fuzzy:
        results = index.fuzzy_lookup(args.fuzzy, source_lang=args.lang)
        if results:
            print(f"Fuzzy matches for '{args.fuzzy}':")
            for entry, score, matched in results:
                print(f"  [{score:.2f}] {entry.english} | {entry.russian} | {entry.german} (matched '{matched}')")
            return 0
        else:
            print(f"No fuzzy matches found for '{args.fuzzy}'.")
            return 1

    print(f"TerminologyIndex loaded with {len(index)} terms.")
    print("Use --lookup <term>, --fuzzy <term>, or --validate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
