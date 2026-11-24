from __future__ import annotations

import os
import unittest

from core.intelligence import enhance_brief, enhance_judgment, llm_enabled, summarize
from core.models import Project, RiskJudgment
from core.llm_client import LLMClient


class IntelligenceFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old = os.environ.get("OPS_USE_LLM")
        os.environ["OPS_USE_LLM"] = "0"

    def tearDown(self) -> None:
        if self.old is None:
            os.environ.pop("OPS_USE_LLM", None)
        else:
            os.environ["OPS_USE_LLM"] = self.old

    def test_llm_disabled_by_default(self) -> None:
        self.assertFalse(llm_enabled())

    def test_judgment_falls_back_to_rules(self) -> None:
        p = Project(path="p.md", title="Demo")
        r = RiskJudgment(level="low", score=20, triggers=[], recommendation="go", needs_approval=False)
        merged, source = enhance_judgment(p, r)
        self.assertEqual(source, "rules")
        self.assertEqual(merged.level, "low")

    def test_brief_falls_back_to_rules(self) -> None:
        p = Project(path="p.md", title="Demo")
        r = RiskJudgment(level="low", score=20, triggers=[], recommendation="go", needs_approval=False)
        out, source = enhance_brief(p, r, "original")
        self.assertEqual(source, "rules")
        self.assertEqual(out, "original")

    def test_summary_falls_back_to_rules(self) -> None:
        out, source = summarize("some text", "fallback")
        self.assertEqual(source, "rules")
        self.assertEqual(out, "fallback")

    def test_client_construction_is_offline_safe(self) -> None:
        client = LLMClient(base_url="http://127.0.0.1:9/v1", api_key="x", model="auto")
        self.assertIsNotNone(client)
        self.assertFalse(client.is_available())


if __name__ == "__main__":
    unittest.main()
