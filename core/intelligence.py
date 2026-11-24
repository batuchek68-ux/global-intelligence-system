"""LLM enhancement layer with rule-based fallback.

All helpers are opt-in via OPS_USE_LLM=1 and degrade silently to the
deterministic rule output when the LLM endpoint is unavailable. This keeps
GitHub Actions (no local LLM) fully functional while local runs can use
FreeLLMAPI for genuine analysis.
"""
from __future__ import annotations

import os
from typing import Any

from core.models import Project, RiskJudgment


def llm_enabled() -> bool:
    return os.getenv("OPS_USE_LLM", "0") == "1"


def _client():
    if not llm_enabled():
        return None
    try:
        from core.llm_client import get_llm_client
        client = get_llm_client()
        return client if client.is_available() else None
    except Exception:
        return None


def enhance_judgment(project: Project, rule: RiskJudgment) -> tuple[RiskJudgment, str]:
    """Return (judgment, source). Falls back to the rule judgment unchanged."""
    client = _client()
    if client is None:
        return rule, "rules"
    try:
        info = (
            f"Title: {project.title}\nCountry: {project.country}\n"
            f"Counterparty: {project.counterparty}\nStage: {project.stage}\n"
            f"Amount: {project.amount}\nLatest communication: {project.latest_communication}\n"
            f"Known risks: {', '.join(project.risks)}\nNext decision: {project.next_decision}"
        )
        result = client.analyze_risk(info, rule.triggers)
        level = str(result.get("risk_level", rule.level)).lower()
        if level not in {"low", "medium", "high"}:
            level = rule.level
        score = rule.score
        if level == "high":
            score = max(score, 80)
        elif level == "low":
            score = min(score, 35)
        merged = RiskJudgment(
            level=level,
            score=score,
            triggers=list(rule.triggers),
            recommendation=str(result.get("recommendation") or rule.recommendation),
            needs_approval=rule.needs_approval or level in {"medium", "high"},
        )
        return merged, "llm+rules"
    except Exception:
        return rule, "rules"


def enhance_brief(project: Project, judgment: RiskJudgment, rule_brief: str) -> tuple[str, str]:
    """Return (brief_text, source). Appends LLM analysis when available."""
    client = _client()
    if client is None:
        return rule_brief, "rules"
    try:
        text = client.generate_brief(
            project.title, project.country, project.counterparty,
            judgment.level, judgment.triggers,
        )
        if not text.strip():
            return rule_brief, "rules"
        return rule_brief + "\n## LLM Analysis\n\n" + text.strip() + "\n", "llm+rules"
    except Exception:
        return rule_brief, "rules"


def summarize(text: str, fallback: str) -> tuple[str, str]:
    client = _client()
    if client is None:
        return fallback, "rules"
    try:
        out = client.summarize(text)
        return (out.strip() or fallback), ("llm" if out.strip() else "rules")
    except Exception:
        return fallback, "rules"
