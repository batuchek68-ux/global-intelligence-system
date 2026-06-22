from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_JSON_RELATIVE = "reports/cloud_acceptance.json"
ACCEPTANCE_MD_RELATIVE = "reports/cloud_acceptance.md"
ACCEPTANCE_JSON = ROOT / ACCEPTANCE_JSON_RELATIVE
ACCEPTANCE_MD = ROOT / ACCEPTANCE_MD_RELATIVE


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_json(relative: str, default: dict | None = None) -> dict:
    path = ROOT / relative
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_file(relative: str) -> dict:
    path = ROOT / relative
    return {
        "name": f"file:{relative}",
        "ok": path.is_file(),
        "evidence": relative if path.is_file() else "missing",
    }


def check_text(relative: str, needle: str) -> dict:
    text = read_text(relative)
    return {
        "name": f"text:{relative}:{needle}",
        "ok": needle in text,
        "evidence": relative if needle in text else f"missing text: {needle}",
    }


def build_acceptance_status() -> dict:
    summary = read_json("memory/last_run.json")
    cases = summary.get("cases", [])
    execution_logs = sorted((ROOT / "memory" / "execution_logs").glob("*.json"))
    waiting_for_owner = [
        case
        for case in cases
        if case.get("classification", {}).get("is_major_matter") and not case.get("owner_decision")
    ]
    autonomous_cases = [
        case
        for case in cases
        if not case.get("classification", {}).get("is_major_matter")
    ]
    resolved_major_matters = [case for case in cases if case.get("owner_decision")]

    checks = [
        check_file(".github/workflows/international_trade_ops.yml"),
        check_file(".github/workflows/owner_decision.yml"),
        check_file(".github/workflows/watchdog.yml"),
        check_file(".github/workflows/cloud_acceptance.yml"),
        check_file("reports/headquarters_status.md"),
        check_file("reports/owner_inbox.md"),
        check_file("reports/watchdog_status.md"),
        check_file("memory/last_run.json"),
        check_text(".github/workflows/international_trade_ops.yml", "python workflows/daily_job.py"),
        check_text(".github/workflows/international_trade_ops.yml", "python workflows/persist_state.py"),
        check_text(".github/workflows/owner_decision.yml", "issue_comment"),
        check_text(".github/workflows/owner_decision.yml", "python workflows/resolve_major_matter.py"),
        check_text(".github/workflows/watchdog.yml", "python workflows/persist_state.py"),
        check_text(".github/workflows/cloud_acceptance.yml", "python workflows/cloud_acceptance.py"),
        check_text("reports/headquarters_status.md", "Execution status"),
        check_text("reports/owner_inbox.md", "Owner Inbox"),
        check_text("reports/watchdog_status.md", "24h Codex Watchdog"),
        {
            "name": "last_run:projects_scanned",
            "ok": summary.get("project_count", 0) > 0,
            "evidence": f"project_count={summary.get('project_count', 0)}",
        },
        {
            "name": "last_run:cases_created",
            "ok": summary.get("case_count", 0) == len(cases) and len(cases) > 0,
            "evidence": f"case_count={summary.get('case_count', 0)}, cases={len(cases)}",
        },
        {
            "name": "execution_logs:one_per_case",
            "ok": len(execution_logs) >= len(cases) > 0,
            "evidence": f"execution_logs={len(execution_logs)}, cases={len(cases)}",
        },
        {
            "name": "owner_boundary:major_matters_identified",
            "ok": summary.get("major_matter_count", 0) >= len(waiting_for_owner),
            "evidence": (
                f"major_matter_count={summary.get('major_matter_count', 0)}, "
                f"waiting_for_owner={len(waiting_for_owner)}"
            ),
        },
        {
            "name": "owner_boundary:resolved_or_waiting",
            "ok": summary.get("major_matter_count", 0) == len(waiting_for_owner) + len(resolved_major_matters),
            "evidence": (
                f"major={summary.get('major_matter_count', 0)}, "
                f"resolved={len(resolved_major_matters)}, waiting={len(waiting_for_owner)}"
            ),
        },
        {
            "name": "codex_autonomy:autonomous_cases_recorded",
            "ok": len(autonomous_cases) > 0,
            "evidence": f"autonomous_cases={len(autonomous_cases)}",
        },
    ]

    ok = all(check["ok"] for check in checks)
    return {
        "ok": ok,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repository": os.getenv("GITHUB_REPOSITORY", "local"),
        "run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "command_model": {
            "github": "cloud AI headquarters",
            "codex": "24h autonomous executive",
            "owner": "decides only major matters",
        },
        "summary": {
            "projects": summary.get("project_count", 0),
            "cases": len(cases),
            "major_matters": summary.get("major_matter_count", 0),
            "resolved_major_matters": len(resolved_major_matters),
            "waiting_for_owner": len(waiting_for_owner),
            "autonomous_cases": len(autonomous_cases),
            "execution_logs": len(execution_logs),
        },
        "checks": checks,
    }


def render_acceptance_report(status: dict) -> str:
    lines = [
        "# GitHub Cloud Acceptance",
        "",
        f"- Status: {'PASS' if status.get('ok') else 'FAIL'}",
        f"- Generated: {status.get('created_at')}",
        f"- Repository: {status.get('repository')}",
        f"- Run id: {status.get('run_id')}",
        "",
        "## Command Model",
        "",
        "- GitHub = cloud AI headquarters",
        "- Codex = 24h autonomous executive",
        "- Owner = decides only major matters",
        "",
        "## Summary",
        "",
    ]
    for key, value in status.get("summary", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Checks", ""])
    for check in status.get("checks", []):
        mark = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- {mark} `{check.get('name')}` - {check.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def publish_to_step_summary(report: str) -> dict:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return {"published": False, "reason": "GITHUB_STEP_SUMMARY not configured"}
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(report)
        handle.write("\n")
    return {"published": True, "summary_path": summary_path}


def run_acceptance() -> dict:
    status = build_acceptance_status()
    ACCEPTANCE_JSON.parent.mkdir(parents=True, exist_ok=True)
    ACCEPTANCE_JSON.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render_acceptance_report(status)
    ACCEPTANCE_MD.write_text(report, encoding="utf-8")
    status["report_path"] = str(ACCEPTANCE_MD)
    status["json_path"] = str(ACCEPTANCE_JSON)
    status["publish"] = publish_to_step_summary(report)
    return status


def main() -> None:
    status = run_acceptance()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if not status.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
