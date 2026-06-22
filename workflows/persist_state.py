from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATE_PATHS = [
    "memory",
    "reports",
    "comm/outbox",
    "research/briefs",
    "media/drafts",
]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))


def git_available() -> bool:
    return run(["git", "--version"]).returncode == 0


def has_changes() -> bool:
    result = run(["git", "status", "--porcelain", "--"] + STATE_PATHS)
    return bool(result.stdout.strip())


def persist_state(message: str | None = None) -> dict:
    if not git_available():
        return {"committed": False, "reason": "git is not available"}

    if not has_changes():
        return {"committed": False, "reason": "no state changes"}

    run(["git", "config", "user.name", "international-trade-ai"])
    run(["git", "config", "user.email", "international-trade-ai@example.local"])

    add_result = run(["git", "add"] + STATE_PATHS)
    if add_result.returncode != 0:
        return {"committed": False, "reason": add_result.stderr.strip() or add_result.stdout.strip()}

    commit_message = message or os.getenv("STATE_COMMIT_MESSAGE") or "Persist International Trade AI state"
    commit_result = run(["git", "commit", "-m", commit_message])
    if commit_result.returncode != 0:
        return {"committed": False, "reason": commit_result.stderr.strip() or commit_result.stdout.strip()}

    push_result = run(["git", "push"])
    if push_result.returncode != 0:
        return {"committed": True, "pushed": False, "reason": push_result.stderr.strip() or push_result.stdout.strip()}

    return {"committed": True, "pushed": True}


def main() -> None:
    result = persist_state()
    print(result)
    if result.get("committed") and result.get("pushed") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
