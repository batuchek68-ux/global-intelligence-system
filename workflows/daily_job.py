from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comm.wechat import build_approval_ticket, maybe_send_webhook, merge_existing_ticket, write_outbox
from comm.github_issue import maybe_create_issue
from content.video_script import build_video_script
from core.executor import build_execution_record
from core.judge import judge_project
from core.models import OperatingCase, now_iso
from core.operator import build_operator_log, classify_matter
from core.planner import plan_actions
from core.project_loader import load_active_projects
from core.report import build_headquarters_report, build_owner_inbox
from core.storage import ensure_dirs, read_json, safe_slug, write_json, write_text
from intelligence.brief_generator import build_research_brief


def run_daily_cycle(projects: list | None = None) -> dict:
    ensure_dirs()
    projects = projects if projects is not None else load_active_projects()
    cases: list[dict] = []

    for project in projects:
        slug = safe_slug(project.title)
        judgment = judge_project(project)
        actions = plan_actions(project, judgment)

        brief = build_research_brief(project, judgment)
        video = build_video_script(project, judgment)
        brief_path = write_text(ROOT / "research" / "briefs" / f"{slug}.md", brief)
        video_path = write_text(ROOT / "media" / "drafts" / f"{slug}.md", video)

        outbox_path = None
        webhook_result = {"sent": False, "reason": "approval not needed"}
        github_issue_result = {"created": False, "reason": "approval not needed"}
        owner_decision = None
        if judgment.needs_approval:
            ticket = build_approval_ticket(project, judgment)
            outbox = ROOT / "comm" / "outbox" / f"{slug}.json"
            existing_ticket = read_json(outbox, None)
            ticket = merge_existing_ticket(ticket, existing_ticket)
            outbox_path = str(write_outbox(ticket, outbox))
            owner_decision = ticket.get("owner_decision")
            if ticket.get("status") == "resolved":
                webhook_result = {"sent": False, "reason": "major matter already resolved"}
                github_issue_result = {"created": False, "reason": "major matter already resolved"}
                actions.append(f"Continue according to owner decision: {owner_decision}.")
            elif existing_ticket and existing_ticket.get("status") == "waiting":
                webhook_result = {"sent": False, "reason": "approval already waiting"}
                github_issue_result = {"created": False, "reason": "approval already waiting"}
            else:
                webhook_result = maybe_send_webhook(ticket)
                github_issue_result = maybe_create_issue(ticket)
                if github_issue_result.get("created"):
                    ticket["github_issue"] = github_issue_result
                    write_outbox(ticket, outbox)

        classification = classify_matter(project, judgment)
        execution_record = build_execution_record(project, judgment, actions, classification, owner_decision)
        execution_log_path = write_json(ROOT / "memory" / "execution_logs" / f"{slug}.json", execution_record)

        operator_log = build_operator_log(project, judgment, actions)
        operator_log_path = write_text(ROOT / "memory" / "operator_logs" / f"{slug}.md", operator_log)

        case = OperatingCase(
            project=project,
            judgment=judgment,
            actions=actions,
            brief_path=str(brief_path),
            video_path=str(video_path),
            outbox_path=outbox_path,
        )
        case_data = case.to_dict()
        case_data["classification"] = classification
        case_data["execution"] = execution_record
        case_data["execution_log_path"] = str(execution_log_path)
        case_data["operator_log_path"] = str(operator_log_path)
        case_data["owner_decision"] = owner_decision
        case_data["webhook"] = webhook_result
        case_data["github_issue"] = github_issue_result
        write_json(ROOT / "memory" / "cases" / f"{slug}.json", case_data)
        cases.append(case_data)

    summary = {
        "created_at": now_iso(),
        "project_count": len(projects),
        "case_count": len(cases),
        "approval_count": sum(1 for item in cases if item["judgment"]["needs_approval"]),
        "major_matter_count": sum(1 for item in cases if item["classification"]["is_major_matter"]),
        "resolved_major_matter_count": sum(1 for item in cases if item.get("owner_decision")),
        "cases": cases,
    }
    write_json(ROOT / "memory" / "last_run.json", summary)
    report = build_headquarters_report(summary)
    write_text(ROOT / "reports" / "headquarters_status.md", report)
    owner_inbox = build_owner_inbox(summary)
    write_text(ROOT / "reports" / "owner_inbox.md", owner_inbox)
    return summary


def main() -> None:
    summary = run_daily_cycle()
    print(
        "International Trade AI cycle complete: "
        f"{summary['case_count']} cases, "
        f"{summary['approval_count']} approvals, "
        f"{summary['major_matter_count']} major matters."
    )
    print(f"Last run: {ROOT / 'memory' / 'last_run.json'}")


if __name__ == "__main__":
    main()
