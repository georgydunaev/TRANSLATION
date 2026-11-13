# Ticket 03: Add Morse-Kelley and formal verification specific terminology

**Project:** TRANSLATION
**Importance:** 3/10
**State:** closed
**Target Model Tier:** Tier 2 / Tier 3 (Free Cloud / Small LLMs)
**Labels:** user, simple-task, tier2-model, tier3-model, TRANSLATION

## Description
Expand `GLOSSARY.md` in `TRANSLATION/` with 25 terms specific to Morse-Kelley class theory, sequent calculus, LCF kernel architecture, and dependent types.

## Acceptance Criteria
1. Implementation is clean, tested, and self-contained within `TRANSLATION/`.
2. Do not modify files outside `TRANSLATION/`.
3. Verify syntax and tests pass without errors.

## Resolution
Resolved. Expanded `GLOSSARY.md` and `glossary.json` with domain-specific formal mathematical terminology across English, Russian, and German:
- Morse-Kelley and NBG class theory: Proper Class, Class Comprehension, Dunaev Tagged Ordered Pair, Tagged Ordered Pair, Kuratowski Ordered Pair, Von Neumann-Bernays-Gödel Set Theory, Well-Founded Relation.
- Proof theory and logic: Sequent Calculus, Cut Elimination, Natural Deduction, Hilbert-Style Deduction System, Deduction Theorem, Modus Ponens, Discharge of Assumptions, Henkin Witness, Herbrand Universe.
- Type theory and constructive logic: Calculus of Inductive Constructions, Formulas-as-Types, Dependent Product (Pi-Type), Dependent Sum (Sigma-Type), Polymorphic Lambda Calculus, Confluence (Church-Rosser), Strong Normalization, Type Inference, Context, Judgment.
- Proof assistants and verified systems: LCF Kernel, CakeML Verified Compiler, Poly/ML Runtime, Isabelle/ZF Object Logic, Pure Isabelle Framework, Proof State, Tactic, Tacticals, Simplifier, Small Inversion.
- Verified in `tests/test_translation.py`.
