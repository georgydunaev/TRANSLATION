#!/usr/bin/env python3
"""LaTeX token protection and mathematical symbol preservation pipeline.

Modular preprocessing step for mathematical LaTeX documents that protects
inline and display math, math environments, macros, citations, escaped characters,
and formal mathematical symbols prior to translation, and restores them intact.
"""

import argparse
import os
import re
import sys
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple


DEFAULT_PLACEHOLDER_PREFIX = "__LATEX_TOKEN_"
DEFAULT_PLACEHOLDER_SUFFIX = "__"

# Primary top-level display math environments
DISPLAY_MATH_ENVIRONMENTS = (
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "flalign",
    "flalign*",
    "alignat",
    "alignat*",
    "displaymath",
)

# Secondary math environments (matrices, cases, arrays, splits)
INTERNAL_MATH_ENVIRONMENTS = (
    "matrix",
    "pmatrix",
    "bmatrix",
    "Bmatrix",
    "vmatrix",
    "Vmatrix",
    "cases",
    "split",
    "array",
    "smallmatrix",
    "subarray",
    "math",
)

# Common verbatim or code environments
VERBATIM_ENVIRONMENTS = (
    "verbatim",
    "verbatim*",
    "lstlisting",
    "minted",
)

# Critical LaTeX macros whose structure should not be modified
CRITICAL_MACROS = (
    "cite",
    "citep",
    "citet",
    "ref",
    "eqref",
    "pageref",
    "label",
    "url",
    "href",
    "includegraphics",
    "bibliography",
    "bibliographystyle",
    "input",
    "include",
    "documentclass",
    "usepackage",
    "newcommand",
    "renewcommand",
    "def",
)

# Common formal mathematical logic and set theory symbols
MATH_SYMBOLS: Tuple[str, ...] = (
    "\\forall",
    "\\exists",
    "\\exists!",
    "\\in",
    "\\notin",
    "\\ni",
    "\\subset",
    "\\subseteq",
    "\\supset",
    "\\supseteq",
    "\\cup",
    "\\cap",
    "\\bigcup",
    "\\bigcap",
    "\\setminus",
    "\\emptyset",
    "\\varnothing",
    "\\land",
    "\\lor",
    "\\neg",
    "\\lnot",
    "\\implies",
    "\\iff",
    "\\rightarrow",
    "\\leftarrow",
    "\\Rightarrow",
    "\\Leftarrow",
    "\\leftrightarrow",
    "\\Leftrightarrow",
    "\\vdash",
    "\\models",
    "\\top",
    "\\bot",
    "\\lambda",
    "\\Pi",
    "\\Sigma",
    "\\omega",
    "\\aleph",
    "\\beth",
    "\\infty",
    "\\leq",
    "\\geq",
    "\\neq",
    "\\equiv",
    "\\approx",
    "\\sim",
    "\\cong",
    "\\times",
    "\\otimes",
    "\\oplus",
    "\\circ",
    "\\cdot",
    "\\dots",
    "\\ldots",
    "\\cdots",
    "\\vdots",
    "\\ddots",
    "\\partial",
    "\\nabla",
    "\\sum",
    "\\prod",
    "\\int",
)

# Unicode mathematical and logical symbols
UNICODE_MATH_SYMBOLS: Tuple[str, ...] = (
    "∀",
    "∃",
    "∄",
    "∈",
    "∉",
    "∋",
    "⊆",
    "⊂",
    "⊇",
    "⊃",
    "∪",
    "∩",
    "∖",
    "∅",
    "∧",
    "∨",
    "¬",
    "⇒",
    "⇔",
    "⊢",
    "⊨",
    "⊤",
    "⊥",
    "λ",
    "Π",
    "Σ",
    "ω",
    "ℵ",
    "ℶ",
    "∞",
    "≤",
    "≥",
    "≠",
    "≡",
    "≈",
    "≅",
    "×",
    "⊗",
    "⊕",
    "⟦",
    "⟧",
    "⟨",
    "⟩",
    "⦃",
    "⦄",
    "‹",
    "›",
    "⦇",
    "⦈",
)


class LatexTokenPreprocessor:
    """Preprocesses LaTeX source by protecting mathematical formulas, environments, and macros.

    Replaces protected segments with non-translatable placeholders and provides
    reliable restoration after translation or linguistic processing.
    """

    def __init__(
        self,
        protect_comments: bool = True,
        protect_verbatim: bool = True,
        protect_environments: bool = True,
        protect_display_math: bool = True,
        protect_inline_math: bool = True,
        protect_macros: bool = True,
        protect_escaped_chars: bool = True,
        protect_math_symbols: bool = True,
        placeholder_prefix: str = DEFAULT_PLACEHOLDER_PREFIX,
        placeholder_suffix: str = DEFAULT_PLACEHOLDER_SUFFIX,
    ):
        self.protect_comments = protect_comments
        self.protect_verbatim = protect_verbatim
        self.protect_environments = protect_environments
        self.protect_display_math = protect_display_math
        self.protect_inline_math = protect_inline_math
        self.protect_macros = protect_macros
        self.protect_escaped_chars = protect_escaped_chars
        self.protect_math_symbols = protect_math_symbols
        self.placeholder_prefix = placeholder_prefix
        self.placeholder_suffix = placeholder_suffix

        # Build regex patterns
        self._compiled_patterns = self._build_patterns()

    def _build_patterns(self):
        """Compile regex patterns ordered by outer-to-inner precedence."""
        patterns: List[Tuple[str, Pattern[str]]] = []

        # 1. Comments: % ... end of line (excluding escaped \%)
        if self.protect_comments:
            patterns.append(
                ("comment", re.compile(r"(?<!\\)%.*$", re.MULTILINE))
            )

        # 2. Verbatim environments
        if self.protect_verbatim:
            env_union = "|".join(re.escape(e) for e in VERBATIM_ENVIRONMENTS)
            patterns.append(
                (
                    "verbatim_env",
                    re.compile(
                        rf"\\begin\{{({env_union})\}}.*?\\end\{{\1\}}",
                        re.DOTALL,
                    ),
                )
            )
            patterns.append(
                (
                    "inline_verb",
                    re.compile(r"\\verb\*?([^a-zA-Z0-9\s]).*?\1"),
                )
            )

        # 3. Outer display math: $$ ... $$ and \[ ... \]
        if self.protect_display_math:
            patterns.append(
                (
                    "display_dollars",
                    re.compile(r"\$\$.*?\$\$", re.DOTALL),
                )
            )
            patterns.append(
                (
                    "display_brackets",
                    re.compile(r"\\\[.*?\\\]", re.DOTALL),
                )
            )

        # 4. Primary display math environments: \begin{equation} ... \end{equation}
        if self.protect_environments:
            disp_env_union = "|".join(re.escape(e) for e in DISPLAY_MATH_ENVIRONMENTS)
            patterns.append(
                (
                    "display_math_env",
                    re.compile(
                        rf"\\begin\{{({disp_env_union})\}}.*?\\end\{{\1\}}",
                        re.DOTALL,
                    ),
                )
            )

        # 5. Internal / auxiliary math environments
        if self.protect_environments:
            internal_env_union = "|".join(re.escape(e) for e in INTERNAL_MATH_ENVIRONMENTS)
            patterns.append(
                (
                    "internal_math_env",
                    re.compile(
                        rf"\\begin\{{({internal_env_union})\}}.*?\\end\{{\1\}}",
                        re.DOTALL,
                    ),
                )
            )

        # 6. Inline math: \( ... \) and $ ... $
        if self.protect_inline_math:
            patterns.append(
                (
                    "inline_parens",
                    re.compile(r"\\\(.*?\\\)", re.DOTALL),
                )
            )
            # Match $ ... $ ensuring not \$ and not $$
            patterns.append(
                (
                    "inline_dollars",
                    re.compile(r"(?<!\\)\$(?!\$)(?:\\\$|[^\$\n])+?(?<!\\)\$"),
                )
            )

        # 7. Critical macros: \cite{...}, \ref{...}, \url{...}, etc.
        if self.protect_macros:
            macro_union = "|".join(re.escape(m) for m in CRITICAL_MACROS)
            patterns.append(
                (
                    "macro_command",
                    re.compile(
                        rf"\\(?:{macro_union})(?:\[[^\]]*\])?\{{[^}}]*\}}",
                    ),
                )
            )

        # 8. Escaped characters: \$, \%, \&, \#, \_, \{, \}
        if self.protect_escaped_chars:
            patterns.append(
                (
                    "escaped_char",
                    re.compile(r"\\[$&#_%{}~^]"),
                )
            )

        # 9. Standalone math symbols
        if self.protect_math_symbols:
            escaped_syms = [re.escape(s) for s in MATH_SYMBOLS]
            patterns.append(
                (
                    "math_symbol_macro",
                    re.compile(r"(?:" + "|".join(escaped_syms) + r")\b"),
                )
            )
            unicode_syms = [re.escape(u) for u in UNICODE_MATH_SYMBOLS]
            patterns.append(
                (
                    "unicode_math_symbol",
                    re.compile(r"(?:" + "|".join(unicode_syms) + r")"),
                )
            )

        return patterns

    def preprocess(self, text: str):
        """Protect LaTeX tokens and return placeholder text and token registry.

        Returns:
            (protected_text, registry)
            where registry maps placeholder to original token text.
        """
        registry: Dict[str, str] = {}
        token_counter = 0

        current_text = text

        for label, pattern in self._compiled_patterns:
            def replacer(match: re.Match):
                nonlocal token_counter
                original_token = match.group(0)
                placeholder = (
                    f"{self.placeholder_prefix}{token_counter}{self.placeholder_suffix}"
                )
                registry[placeholder] = original_token
                token_counter += 1
                return placeholder

            current_text = pattern.sub(replacer, current_text)

        return current_text, registry

    def restore(
        self,
        protected_text: str,
        registry: Dict[str, str],
        tolerant: bool = True,
    ):
        """Restore protected placeholders back to their original LaTeX tokens.

        Restores recursively in reverse order of token generation to guarantee
        that nested placeholders (if any) are fully expanded.
        """
        if not registry:
            return protected_text

        result = protected_text

        # Sort token keys in reverse numerical order
        def get_index(k: str):
            m = re.search(r"\d+", k)
            return int(m.group(0)) if m else -1

        sorted_keys = sorted(registry.keys(), key=get_index, reverse=True)

        tolerant_pattern = re.compile(
            r"__\s*LATEX_TOKEN_?\s*(\d+)\s*__",
            re.IGNORECASE,
        )

        max_passes = 10
        for _ in range(max_passes):
            changed = False

            if tolerant:
                def tolerant_sub(match: re.Match):
                    nonlocal changed
                    idx = match.group(1)
                    canonical = f"{self.placeholder_prefix}{idx}{self.placeholder_suffix}"
                    if canonical in registry:
                        changed = True
                        return registry[canonical]
                    return match.group(0)

                new_result = tolerant_pattern.sub(tolerant_sub, result)
                if new_result != result:
                    result = new_result
                    changed = True

            # Direct replacement for exact keys
            for placeholder in sorted_keys:
                if placeholder in result:
                    result = result.replace(placeholder, registry[placeholder])
                    changed = True

            if not changed:
                break

        return result

    def extract_math_tokens(self, text: str):
        """Extract all mathematical tokens without modifying the text."""
        extracted: List[Dict[str, Any]] = []

        for label, pattern in self._compiled_patterns:
            for match in pattern.finditer(text):
                extracted.append({
                    "type": label,
                    "token": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                })

        extracted.sort(key=lambda x: x["start"])
        return extracted

    def verify_roundtrip(self, text: str):
        """Verify that text survives preprocess and restore without corruption."""
        protected, registry = self.preprocess(text)
        restored = self.restore(protected, registry)
        if text == restored:
            return True, "Roundtrip verification successful."
        return False, f"Restored text differs from original. Diff length: {abs(len(text) - len(restored))}"


class MathSymbolProtectionPipeline:
    """Configurable pipeline for mathematical symbol protection and restoration."""

    def __init__(self, preprocessor: Optional[LatexTokenPreprocessor] = None):
        self.preprocessor = preprocessor or LatexTokenPreprocessor()
        self.custom_substitutions: Dict[str, str] = {}

    def register_symbol(self, symbol: str):
        """Register a custom symbol to preserve during translation."""
        if symbol not in MATH_SYMBOLS:
            escaped = re.escape(symbol)
            pattern = re.compile(rf"{escaped}")
            self.preprocessor._compiled_patterns.append(("custom_symbol", pattern))

    def protect(self, text: str):
        """Execute protection pipeline."""
        return self.preprocessor.preprocess(text)

    def restore(self, text: str, registry: Dict[str, str]):
        """Execute restoration pipeline."""
        return self.preprocessor.restore(text, registry)


def preprocess_latex_tokens(
    text: str,
    protect_comments: bool = True,
    protect_environments: bool = True,
    protect_display_math: bool = True,
    protect_inline_math: bool = True,
    protect_macros: bool = True,
    protect_escaped_chars: bool = True,
    protect_math_symbols: bool = True,
):
    """Standard entrypoint for LaTeX token and mathematical symbol protection.

    Returns:
        (protected_text, token_registry)
    """
    preprocessor = LatexTokenPreprocessor(
        protect_comments=protect_comments,
        protect_environments=protect_environments,
        protect_display_math=protect_display_math,
        protect_inline_math=protect_inline_math,
        protect_macros=protect_macros,
        protect_escaped_chars=protect_escaped_chars,
        protect_math_symbols=protect_math_symbols,
    )
    return preprocessor.preprocess(text)


def restore_latex_tokens(
    protected_text: str,
    registry: Dict[str, str],
    tolerant: bool = True,
):
    """Standard entrypoint for LaTeX token and mathematical symbol restoration."""
    preprocessor = LatexTokenPreprocessor()
    return preprocessor.restore(protected_text, registry, tolerant=tolerant)


def main():
    parser = argparse.ArgumentParser(
        description="LaTeX Token Preprocessor and Mathematical Symbol Protection Tool"
    )
    parser.add_argument("--file", help="Path to LaTeX file to preprocess")
    parser.add_argument("--roundtrip", action="store_true", help="Verify roundtrip restoration")
    parser.add_argument("--stats", action="store_true", help="Display token statistics")

    args = parser.parse_args()

    if not args.file:
        print("Usage: python3 latex_token_preprocessor.py --file <path> [--roundtrip] [--stats]")
        return 0

    if not os.path.isfile(args.file):
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    with open(args.file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    preprocessor = LatexTokenPreprocessor()
    protected, registry = preprocessor.preprocess(content)

    print(f"File processed: {args.file}")
    print(f"Total tokens protected: {len(registry)}")

    if args.stats:
        tokens = preprocessor.extract_math_tokens(content)
        type_counts: Dict[str, int] = {}
        for t in tokens:
            type_counts[t["type"]] = type_counts.get(t["type"], 0) + 1
        print("Token category counts:")
        for category, count in sorted(type_counts.items()):
            print(f"  {category}: {count}")

    if args.roundtrip:
        ok, msg = preprocessor.verify_roundtrip(content)
        print(f"Roundtrip check: {'PASSED' if ok else 'FAILED'} - {msg}")
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
