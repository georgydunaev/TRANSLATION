#!/usr/bin/env python3
"""Verification tests for TRANSLATION (translation.tex macro and environment consistency)."""

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestTranslation(unittest.TestCase):
    def test_translation_tex_exists_and_balanced_environments(self):
        tex_path = os.path.join(ROOT, "translation.tex")
        self.assertTrue(os.path.isfile(tex_path))
        with open(tex_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        self.assertGreater(len(content), 100)
        begins = re.findall(r"\\begin\{([^}]+)\}", content)
        ends = re.findall(r"\\end\{([^}]+)\}", content)
        self.assertEqual(len(begins), len(ends))


if __name__ == "__main__":
    unittest.main()
