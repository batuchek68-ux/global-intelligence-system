from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.preflight_check import check as preflight_check
from workflows.cloud_config import configured_repository, configured_token_info, load_cloud_config, valid_repository_name

STATUS_JSON_RELATIVE = "reports/cloud_test_status.json"
STATUS_MD_RELATIVE = "reports/cloud_test_status.md"
STATUS_JSON = ROOT / STATUS_JSON_RELATIVE
STATUS_MD = ROOT / STATUS_MD_RELATIVE


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(relative: str) -> dict:
    path = ROOT / relative
    if not path.exists():
        return {"exists": False, "path": relative}
    try:
        return {"exists": True, "path": relative, "data": json.loads(path.read_text(encoding="utf-8"))}
    except json.JSONDecodeError as exc:
        return {"exists": True, "path": relative, "error": str(exc)}


def env_status() -> dict:
    env_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    token, source = configured_token_info(env_token)
    config = load_cloud_config()
    repository = configured_repository(os.getenv("GITHUB_REPOSITORY"))
    return {
        "token_configured": bool(token),
        "token_source": source,
        "repository_configured": valid_repository_name(repository),
        "repository": repository,
        "local_config": config,
    }


def build_status() -> dict:
    env_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    token, source = configured_token_info(env_token)
    config = load_cloud_config()
    repository = configured_repository(os.getenv("GITHUB_REPOSITORY"))
    preflight = preflight_check()
    connection_check = load_json("reports/cloud_connection_check.json")
    cloud_run = load_json("reports/cloud_run.json")
    remote_acceptance = load_json("reports/cloud_acceptance_remote.json")

    cloud_run_data = cloud_run.get("data", {}) if cloud_run.get("exists") else {}
    cloud_run_ok = bool(cloud_run_data.get("ok")) if isinstance(cloud_run_data, dict) else False
    cloud_run_accepted = cloud_run_ok and cloud_run_data.get("stage") == "accepted"

    remote_data = remote_acceptance.get("data", {}) if remote_acceptance.get("exists") else {}
    remote_ok = bool(remote_data.get("ok")) if isinstance(remote_data, dict) else False
    remote_success = remote_ok and remote_data.get("conclusion") == "success"

    missing = []
    if not token:
        missing.append("GITHUB_TOKEN or GH_TOKEN")
    if not valid_repository_name(repository):
        missing.append("GITHUB_REPOSITORY")

    local_ready = bool(preflight.get("ok"))
    cloud_ready = local_ready and not missing
    complete = cloud_ready and cloud_run_accepted and remote_success

    return {
        "ok": complete,
        "created_at": now_iso(),
        "stage": "completed" if complete else ("configuration" if missing else "remote_acceptance"),
        "local_ready": local_ready,
        "cloud_ready": cloud_ready,
        "missing": missing,
        "environment": env_status(),
        "token_source": source,
        "local_config": config,
        "next_command": ".\\run-cloud-test.cmd -CreateRepo",
        "interactive_command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\setup-cloud-test.ps1",
        "root_check_command": ".\\check-cloud-config-from-root.cmd",
        "root_next_command": ".\\run-cloud-test-from-root.cmd -CreateRepo",
        "root_interactive_command": ".\\setup-cloud-test-from-root.cmd",
        "token_setup_doc": "docs/github-token-setup.md",
        "completion_evidence_required": [
            "reports/cloud_run.json has ok: true and stage: accepted",
            "reports/cloud_acceptance_remote.json has ok: true and conclusion: success",
            "GitHub Actions run URL is present",
            "remote reports/cloud_acceptance.md says PASS",
        ],
        "preflight": {"ok": preflight.get("ok")},
        "connection_check": connection_check,
        "cloud_run": cloud_run,
        "remote_acceptance": remote_acceptance,
    }


def render_status(status: dict) -> str:
    lines = [
        "# Cloud Test Status",
        "",
        f"- Status: {'PASS' if status['ok'] else 'BLOCKED'}",
        f"- Stage: `{status['stage']}`",
        f"- Local ready: `{status['local_ready']}`",
        f"- Cloud config ready: `{status['cloud_ready']}`",
        "",
        "## Missing",
    ]
    missing = status.get("missing") or []
    if missing:
        lines.extend(f"- `{item}`" for item in missing)
    else:
        lines.append("- None")

    connection_data = status.get("connection_check", {}).get("data", {})
    if isinstance(connection_data, dict) and connection_data.get("exists") is not False:
        connection_missing = connection_data.get("missing") or []
        root_commands = connection_data.get("root_commands") or []
        token_storage = connection_data.get("token_storage")
        if connection_missing or root_commands or token_storage:
            lines.extend(["", "## Connection Check Details"])
            if connection_missing:
                lines.append("")
                lines.append("Missing from connection check:")
                lines.extend(f"- `{item}`" for item in connection_missing)
            if token_storage:
                lines.extend(["", f"Token handling: {token_storage}"])
            if root_commands:
                lines.extend(["", "Root commands:", "", "```powershell"])
                lines.extend(root_commands)
                lines.append("```")

    lines.extend(
        [
            "",
            "## Next Commands",
            "",
            "Use real values only. Do not copy placeholder text such as `owner/repository`, `yourname/...`, or Chinese example words.",
            "",
            "From the organized project root:",
            "",
            "```powershell",
            status["root_check_command"],
            status["root_interactive_command"],
            status["root_next_command"],
            "```",
            "",
            "From the source project directory:",
            "",
            "Token setup details: `docs/github-token-setup.md`",
            "",
            "```powershell",
            status["interactive_command"],
            "```",
            "",
            "or:",
            "",
            "```powershell",
            '$env:GITHUB_TOKEN = "ghp_real_token_here"',
            '$env:GITHUB_REPOSITORY = "real-github-login/international-trade-ai"',
            status["next_command"],
            "```",
            "",
            "## Completion Evidence Required",
        ]
    )
    lines.extend(f"- {item}" for item in status["completion_evidence_required"])
    lines.append("")
    return "\n".join(lines)


def write_reports(status: dict) -> None:
    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    STATUS_MD.write_text(render_status(status), encoding="utf-8")


def main() -> None:
    status = build_status()
    write_reports(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if not status["ok"]:
        raise SystemExit(1 if status.get("stage") != "configuration" else 2)


if __name__ == "__main__":
    main()
