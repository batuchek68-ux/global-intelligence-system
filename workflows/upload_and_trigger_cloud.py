from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.prepare_release import collect_files
from workflows.cloud_config import configured_repository, configured_token
from workflows.trigger_cloud_acceptance import trigger_cloud_acceptance

REPORT_RELATIVE = "reports/cloud_upload_and_acceptance.json"
REPORT = ROOT / REPORT_RELATIVE

SKIP_UPLOAD_PARTS = {"dist"}
SKIP_UPLOAD_FILES = {
    "reports/cloud_acceptance_remote.json",
    REPORT_RELATIVE,
}


def github_contents_request(
    method: str,
    repository: str,
    path: str,
    token: str,
    payload: dict | None = None,
) -> tuple[int, dict | str | None]:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    encoded_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/contents/{encoded_path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            if not body:
                return response.status, None
            return response.status, json.loads(body)
    except Exception as exc:
        if hasattr(exc, "read"):
            body = exc.read().decode("utf-8")
            try:
                return getattr(exc, "code", 0), json.loads(body) if body else {}
            except json.JSONDecodeError:
                return getattr(exc, "code", 0), body
        return 0, str(exc)


def uploadable_files() -> list[Path]:
    files = []
    for path in collect_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative in SKIP_UPLOAD_FILES:
            continue
        if any(part in SKIP_UPLOAD_PARTS for part in Path(relative).parts):
            continue
        files.append(path)
    return files


def get_existing_sha(repository: str, token: str, relative: str, branch: str) -> str | None:
    query = urllib.parse.urlencode({"ref": branch})
    status, data = github_contents_request("GET", repository, f"{relative}?{query}", token)
    if status == 200 and isinstance(data, dict):
        return data.get("sha")
    return None


def upload_file(repository: str, token: str, path: Path, branch: str, message_prefix: str) -> dict:
    relative = path.relative_to(ROOT).as_posix()
    sha = get_existing_sha(repository, token, relative, branch)
    payload = {
        "message": f"{message_prefix}: {relative}",
        "content": base64.b64encode(path.read_bytes()).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    status, data = github_contents_request("PUT", repository, relative, token, payload)
    return {
        "path": relative,
        "ok": status in (200, 201),
        "status": status,
        "action": "updated" if sha else "created",
        "details": data if status not in (200, 201) else None,
    }


def upload_repository(
    repository: str,
    token: str,
    branch: str,
    message_prefix: str,
    max_files: int | None = None,
) -> dict:
    files = uploadable_files()
    if max_files is not None:
        files = files[:max_files]
    results = []
    for index, path in enumerate(files, start=1):
        results.append(upload_file(repository, token, path, branch, message_prefix))
        if index % 10 == 0:
            time.sleep(1)
    return {
        "ok": all(item["ok"] for item in results),
        "file_count": len(files),
        "uploaded": sum(1 for item in results if item["ok"]),
        "failed": [item for item in results if not item["ok"]],
        "results": results,
    }


def upload_and_trigger(
    repository: str,
    token: str,
    branch: str = "main",
    confirm_upload: bool = False,
    trigger: bool = True,
    max_files: int | None = None,
) -> dict:
    if not confirm_upload:
        return {
            "ok": False,
            "stage": "confirmation",
            "reason": "Pass --confirm-upload to upload files to the GitHub repository.",
        }
    upload = upload_repository(
        repository=repository,
        token=token,
        branch=branch,
        message_prefix="Upload International Trade AI cloud headquarters",
        max_files=max_files,
    )
    result = {
        "ok": upload["ok"],
        "stage": "uploaded",
        "repository": repository,
        "branch": branch,
        "upload": upload,
    }
    if upload["ok"] and trigger:
        # GitHub may need a brief moment before the workflow file is dispatchable.
        time.sleep(5)
        result["acceptance"] = trigger_cloud_acceptance(repository, token, ref=branch)
        result["ok"] = bool(result["acceptance"].get("ok"))
        result["stage"] = "accepted" if result["ok"] else "acceptance_failed"
    return result


def write_report(result: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload this project to GitHub via REST API and trigger cloud acceptance.")
    parser.add_argument("--repository", default=configured_repository(os.getenv("GITHUB_REPOSITORY")), help="GitHub repository as owner/name.")
    parser.add_argument("--branch", default=os.getenv("GITHUB_REF_NAME", "main"))
    parser.add_argument("--confirm-upload", action="store_true")
    parser.add_argument("--no-trigger", action="store_true", help="Upload only; do not trigger cloud acceptance.")
    parser.add_argument("--max-files", type=int, default=None, help="Testing aid: upload only the first N files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    token = configured_token(os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"))
    if not token or not args.repository:
        result = {
            "ok": False,
            "stage": "configuration",
            "reason": "Set GITHUB_TOKEN or GH_TOKEN, and GITHUB_REPOSITORY or --repository owner/name.",
        }
        write_report(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    result = upload_and_trigger(
        repository=args.repository,
        token=token,
        branch=args.branch,
        confirm_upload=args.confirm_upload,
        trigger=not args.no_trigger,
        max_files=args.max_files,
    )
    write_report(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
