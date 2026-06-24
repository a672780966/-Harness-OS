#!/usr/bin/env python3
"""Harness Code Copilot — Thin CLI Skeleton.

Usage:
  harness copilot inspect <project_path>
  harness copilot diff-summary <project_path> [--diff-ref=<ref>]
  harness copilot task-card <project_path> [--diff-ref=<ref>]
  harness copilot readiness <project_path> [--diff-ref=<ref>]
  harness copilot agent-state <project_path> [--diff-ref=<ref>] [--format=markdown|json]
  harness copilot agent-state-from-loop <loop_run_dir> [--format=markdown|json]
  harness copilot pr-pack <project_path> [--out=<dir>]
  harness copilot pr-pack-from-loop <loop_run_dir> [--out=<dir>]
  harness copilot pr-comment <project_path> [--format=markdown|json]
  harness copilot pr-comment-from-loop <loop_run_dir> [--format=markdown|json]
  harness copilot live-events <project_path>
  harness copilot live-events-from-loop <loop_run_dir>
  harness copilot live-server <project_path> [--host=127.0.0.1] [--port=8765] [--once]
  harness copilot live-dashboard <project_path> [--out=<dir>]
  harness copilot live-dashboard-from-loop <loop_run_dir> [--out=<dir>]
  harness copilot provider-status [--check] [--format=markdown|json]
  harness copilot config init
  harness copilot config show [--project=<path>]
  harness copilot config path [--project=<path>]
  harness copilot config validate [--project=<path>]
  harness copilot doctor
  harness copilot version

All commands are read-only. No code modification, no external agent control.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for direct invocation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from harness.copilot.view_models import build_dashboard
from harness.copilot.markdown_renderer import (
    render_dashboard, render_modules, render_task_cards,
    render_readiness, render_changes,
)
from harness.copilot.json_renderer import (
    render_dashboard_json, render_modules_json,
    render_task_cards_json, render_readiness_json, render_changes_json,
    is_json_serializable,
)
from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
from harness.copilot.integration.loop_to_copilot_mapper import artifacts_to_dashboard
from harness.copilot.integration.eval_mapper import eval_to_repair_task_cards
from harness.copilot.integration.review_mapper import review_to_repair_task_cards
from harness.copilot.integration.repair_history_mapper import repair_history_to_task_cards
from harness.copilot.integration.final_gate_mapper import final_gate_to_readiness

from harness.copilot.schemas import (
    MergeReadinessState,
    now_iso,
    to_json,
)
from harness.copilot.project_scanner import scan_project
from harness.copilot.event_collector import (
    get_git_diff,
    get_git_diff_stat,
    get_git_status,
    get_git_branch,
    is_git_repo,
)
from harness.copilot.diff_analyzer import parse_diff, group_diff_by_module, simple_diff_stats
from harness.copilot.change_explainer import explain_diff, quick_explain
from harness.copilot.risk_classifier import generate_risk_alerts
from harness.copilot.task_card import (
    from_change_explanations,
    from_risk_alerts,
    from_suggestions,
    generate_summary,
)
from harness.copilot.suggestion_engine import generate_suggestions, quick_suggestions
from harness.copilot.merge_readiness import evaluate_merge_readiness, merge_readiness_to_dict
from harness.copilot.evidence_pack import build_from_task_cards


def cmd_inspect(args: argparse.Namespace) -> None:
    """Inspect a project and show semantic map overview."""
    project_root = os.path.abspath(args.project_path)

    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Inspecting: {project_root}", file=sys.stderr)

    sem_map = scan_project(project_root)

    # Summary
    print(f"\n📁 Project: {sem_map.project_name}")
    print(f"   Files: {sem_map.total_files}")
    print(f"   Lines: {sem_map.total_lines:,}")
    print(f"   Modules: {len(sem_map.modules)}")
    print(f"   Languages: {', '.join(f'{lang}={count}' for lang, count in sorted(sem_map.languages.items(), key=lambda x: -x[1])[:5])}")

    # Git info
    if is_git_repo(project_root):
        branch = get_git_branch(project_root)
        status = get_git_status(project_root)
        print(f"   Git: {branch} ({len(status)} uncommitted)")
    else:
        print("   Git: not a git repository")

    # Risk overview
    high_risk_modules = [m for m in sem_map.modules if m.risk_score >= 0.5]
    if high_risk_modules:
        print(f"\n⚠  High-risk modules:")
        for mod in high_risk_modules:
            print(f"   - {mod.name} (score: {mod.risk_score:.1f})")

    # Full JSON output
    if args.json:
        print("\n" + to_json(sem_map))


def cmd_diff_summary(args: argparse.Namespace) -> None:
    """Show diff summary for recent changes."""
    project_root = os.path.abspath(args.project_path)

    diff_ref = args.diff_ref or "HEAD~1"

    diff_text = get_git_diff(project_root, base_ref=diff_ref)
    if not diff_text:
        print(f"No diff found for {diff_ref} in {project_root}")
        sys.exit(1)

    try:
        sem_map = scan_project(project_root)
    except Exception:
        sem_map = None

    if args.quick or not sem_map:
        output = quick_explain(diff_text)
        print(output)
    else:
        explanations = explain_diff(diff_text, sem_map)
        for expl in explanations:
            print(f"\n[{expl.module}] {expl.summary}")
            print(f"  Intent: {expl.intent}")
            if expl.risks:
                for risk in expl.risks:
                    print(f"  ⚠  {risk}")

    if args.json:
        stats = simple_diff_stats(diff_text)
        print("\n" + json.dumps(stats, indent=2))


def cmd_task_card(args: argparse.Namespace) -> None:
    """Generate task cards from project analysis."""
    project_root = os.path.abspath(args.project_path)

    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Scan project
    sem_map = scan_project(project_root)

    # Get diff
    diff_ref = args.diff_ref or "HEAD~1"
    diff_text = get_git_diff(project_root, base_ref=diff_ref)

    cards = []

    # 1. Risk-based cards
    if diff_text:
        entries = parse_diff(diff_text)
        summaries = group_diff_by_module(entries, sem_map)
        alerts = generate_risk_alerts(summaries, sem_map)
        cards.extend(from_risk_alerts(alerts))

    # 2. Change-based review cards
    if diff_text:
        explanations = explain_diff(diff_text, sem_map)
        cards.extend(from_change_explanations(explanations))

    # 3. Suggestions
    suggestions = generate_suggestions(project_root, sem_map, diff_text)
    cards.extend(from_suggestions(suggestions))

    # Summary
    summary = generate_summary(cards)
    print(f"📋 Task Cards: {summary['summary_line']}")
    print(f"   Critical: {summary['by_priority'].get('critical', 0)}, "
          f"High: {summary['by_priority'].get('high', 0)}, "
          f"Medium: {summary['by_priority'].get('medium', 0)}, "
          f"Low: {summary['by_priority'].get('low', 0)}")

    # Print blocking cards
    blocking = [c for c in cards if c.merge_readiness in (MergeReadinessState.BLOCK, "block")]
    if blocking:
        print(f"\n🔴 Blocking ({len(blocking)}):")
        for card in blocking:
            print(f"   - [{card.priority.value}] {card.title} ({card.card_type.value})")

    # Print all cards if verbose
    if args.verbose:
        print(f"\n--- All Cards ({len(cards)}) ---")
        for card in cards:
            print(f"  [{card.state.value}] {card.title}")
            print(f"       Type: {card.card_type.value}, Priority: {card.priority.value}")
            if card.module:
                print(f"       Module: {card.module}")
            if card.target_file:
                print(f"       File: {card.target_file}")

    if args.json:
        output = {
            "summary": summary,
            "cards": [{
                "card_id": c.card_id,
                "title": c.title,
                "card_type": c.card_type.value,
                "state": c.state.value,
                "priority": c.priority.value,
                "module": c.module,
                "target_file": c.target_file,
                "risk_score": c.risk_score,
                "merge_readiness": c.merge_readiness.value if hasattr(c.merge_readiness, "value") else c.merge_readiness,
                "blocking_issues": c.blocking_issues,
            } for c in cards],
        }
        print("\n" + json.dumps(output, indent=2))


def cmd_readiness(args: argparse.Namespace) -> None:
    """Evaluate merge readiness."""
    project_root = os.path.abspath(args.project_path)

    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Scan project
    sem_map = scan_project(project_root)

    # Get diff and risk
    diff_ref = args.diff_ref or "HEAD~1"
    diff_text = get_git_diff(project_root, base_ref=diff_ref)

    cards = []
    if diff_text:
        entries = parse_diff(diff_text)
        summaries = group_diff_by_module(entries, sem_map)
        alerts = generate_risk_alerts(summaries, sem_map)
        cards.extend(from_risk_alerts(alerts))

        explanations = explain_diff(diff_text, sem_map)
        cards.extend(from_change_explanations(explanations))

    suggestions = generate_suggestions(project_root, sem_map, diff_text)
    cards.extend(from_suggestions(suggestions))

    # Extract risk alerts for readiness eval
    risk_alerts = []
    if diff_text:
        entries = parse_diff(diff_text)
        summaries = group_diff_by_module(entries, sem_map)
        risk_alerts = generate_risk_alerts(summaries, sem_map)

    readiness = evaluate_merge_readiness(
        task_cards=cards,
        risk_alerts=risk_alerts,
        tests_passed=None,  # Not running real tests
        branch_name=get_git_branch(project_root),
    )

    # Output
    state_icon = {
        MergeReadinessState.PASS: "✅",
        MergeReadinessState.BLOCK: "🔴",
        MergeReadinessState.REVIEW_NEEDED: "🟡",
    }.get(readiness.state, "❓")

    print(f"{state_icon} Merge Readiness: {readiness.state.value}")
    print(f"   {readiness.summary}")
    if readiness.blocking_issues:
        print(f"\n   Blocking Issues ({len(readiness.blocking_issues)}):")
        for issue in readiness.blocking_issues:
            print(f"     - {issue}")
    print(f"\n   Review required: {readiness.review_required}")
    print(f"   Pending task cards: {readiness.pending_task_cards}")
    print(f"   High-risk files: {len(readiness.high_risk_changes)}")

    if args.json:
        print("\n" + json.dumps(merge_readiness_to_dict(readiness), indent=2))


# ======================== UX Layer Commands ========================


def cmd_dashboard(args: argparse.Namespace) -> None:
    """Render the full Copilot dashboard."""
    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    dashboard = build_dashboard(project_root, diff_ref=args.diff_ref)

    if args.format == "json":
        print(render_dashboard_json(dashboard))
    elif args.format == "markdown":
        print(render_dashboard(dashboard))
    else:
        # Default: markdown
        print(render_dashboard(dashboard))


def cmd_ux_modules(args: argparse.Namespace) -> None:
    """Render module cards with user-friendly output."""
    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    dashboard = build_dashboard(project_root, diff_ref=args.diff_ref)

    if args.format == "json":
        print(render_modules_json(dashboard.modules))
    elif args.format == "markdown":
        print(render_modules(dashboard.modules))
    else:
        print(render_modules(dashboard.modules))


def cmd_ux_task_cards(args: argparse.Namespace) -> None:
    """Render task cards with user-friendly output."""
    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    dashboard = build_dashboard(project_root, diff_ref=args.diff_ref)
    if not dashboard.task_cards:
        print("No task cards generated.")
        return

    if args.format == "json":
        print(render_task_cards_json(dashboard.task_cards))
    elif args.format == "markdown":
        print(render_task_cards(dashboard.task_cards))
    else:
        print(render_task_cards(dashboard.task_cards))


def cmd_ux_readiness(args: argparse.Namespace) -> None:
    """Render merge readiness with user-friendly output."""
    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    dashboard = build_dashboard(project_root, diff_ref=args.diff_ref)
    if not dashboard.readiness:
        print("No merge readiness evaluation available.")
        return

    if args.format == "json":
        print(render_readiness_json(dashboard.readiness))
    elif args.format == "markdown":
        print(render_readiness(dashboard.readiness))
    else:
        print(render_readiness(dashboard.readiness))


# ==================== Integration Layer Commands ====================


def cmd_from_loop(args: argparse.Namespace) -> None:
    """Load loop artifacts and render Copilot dashboard."""
    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    artifacts = load_loop_artifacts(run_dir)
    if artifacts.load_errors:
        print(f"Warning: {len(artifacts.load_errors)} load error(s)", file=sys.stderr)

    dashboard = artifacts_to_dashboard(artifacts)

    if args.format == "json":
        print(render_dashboard_json(dashboard))
    else:
        print(render_dashboard(dashboard))


def cmd_evidence(args: argparse.Namespace) -> None:
    """Show evidence pack from a loop run."""
    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    artifacts = load_loop_artifacts(run_dir)
    dashboard = artifacts_to_dashboard(artifacts)

    if dashboard.evidence:
        if args.format == "json":
            import json as _json
            print(_json.dumps(dashboard.evidence.to_dict(), indent=2, ensure_ascii=False))
        else:
            from harness.copilot.markdown_renderer import render_evidence
            print(render_evidence(dashboard.evidence))
    else:
        print("No evidence pack available.")


def cmd_repair_cards(args: argparse.Namespace) -> None:
    """Show repair task cards from a loop run."""
    run_dir = os.path.abspath(args.loop_run_dir)
    # ... same as before ...
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    artifacts = load_loop_artifacts(run_dir)
    eval_cards = eval_to_repair_task_cards(artifacts)
    review_cards = review_to_repair_task_cards(artifacts)
    history_cards = repair_history_to_task_cards(artifacts)

    all_cards = eval_cards + review_cards + history_cards

    if not all_cards:
        print("No repair task cards. All checks passed."  if args.format != "json" else "[]")
        return

    if args.format == "json":
        import json as _json
        from harness.copilot.view_models import TaskCardViewModel
        cards_data = [TaskCardViewModel.from_kernel(c).to_dict() for c in all_cards]
        print(_json.dumps({"repair_cards": cards_data}, indent=2, ensure_ascii=False))
    else:
        from harness.copilot.view_models import TaskCardViewModel
        cards_vm_list = [TaskCardViewModel.from_kernel(c) for c in all_cards]
        from harness.copilot.markdown_renderer import render_task_cards
        # Build a simple TaskCardListViewModel
        from harness.copilot.view_models import TaskCardListViewModel as TCLVM
        tc_list = TCLVM(cards=cards_vm_list)
        print(render_task_cards(tc_list))


# =================== Phase 4: MVP Shell Commands ====================


def cmd_shell(args: argparse.Namespace) -> None:
    """Generate a local static HTML dashboard for a project."""
    from harness.copilot.shell.shell_builder import build_project_shell

    out_dir = args.out or os.path.join(args.project_path, ".harness", "copilot_dashboard")
    result = build_project_shell(
        project_path=args.project_path,
        output_dir=out_dir,
        diff_ref=args.diff_ref,
    )

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ HTML dashboard generated")
    print(f"   路径: file://{result['html_path']}")
    print(f"   JSON: {result['json_path']}")
    print(f"   输出目录: {result['output_dir']}")


def cmd_shell_from_loop(args: argparse.Namespace) -> None:
    """Generate a static HTML dashboard from a loop run directory."""
    from harness.copilot.shell.loop_shell_builder import build_loop_shell

    out_dir = args.out or os.path.join(args.loop_run_dir, "..", "..", "copilot_dashboard")
    out_dir = os.path.abspath(out_dir)  # Resolve .. in path
    result = build_loop_shell(
        loop_run_dir=args.loop_run_dir,
        output_dir=out_dir,
    )

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Loop dashboard generated")
    print(f"   路径: file://{result['html_path']}")
    print(f"   JSON: {result['json_path']}")
    print(f"   输出目录: {result['output_dir']}")


def cmd_export_task_card(args: argparse.Namespace) -> None:
    """Export a task card as markdown."""
    import json as _json
    from harness.copilot.shell.copy_text_renderer import (
        export_task_card_markdown,
        export_all_task_cards_markdown,
        render_task_card_copy_text,
    )

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Build dashboard to get task cards
    from harness.copilot.view_models import build_dashboard
    dashboard = build_dashboard(project_root, diff_ref=args.diff_ref)

    if not dashboard.task_cards or not dashboard.task_cards.cards:
        print("No task cards available for export.")
        sys.exit(1)

    cards_dicts = [c.to_dict() for c in dashboard.task_cards.cards]

    if args.card_index is not None:
        # Export single card by index
        try:
            card = cards_dicts[args.card_index]
        except IndexError:
            print(f"Error: Card index {args.card_index} out of range (0-{len(cards_dicts)-1})", file=sys.stderr)
            sys.exit(1)

        md = export_task_card_markdown(card)

        out_path = args.out
        if not out_path:
            # Default filename
            safe_name = card.get("title", "task-card").replace(" ", "-").replace("/", "-")[:40]
            out_path = os.path.join(os.getcwd(), f"{safe_name}.md")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ Task card exported to: {out_path}")

        # Also show copy text in terminal
        print(f"\n--- Copy text ---")
        print(render_task_card_copy_text(card))
    else:
        # Export all cards
        md = export_all_task_cards_markdown(cards_dicts)
        out_path = args.out or os.path.join(os.getcwd(), "task-cards.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ All task cards exported to: {out_path}")


def cmd_preview(args: argparse.Namespace) -> None:
    """Start local read-only preview server for a dashboard directory."""
    from harness.copilot.shell.preview_server import serve_preview
    serve_preview(directory=args.dashboard_dir, port=args.port)


# =================== Phase 6B: Agent State CLI Commands ====================


def cmd_agent_state(args: argparse.Namespace) -> None:
    """Show inferred agent lifecycle state for a project."""
    from harness.copilot.view_models import build_dashboard
    from harness.copilot.agent_state.renderer import render_agent_state

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    dashboard = build_dashboard(project_root, diff_ref=args.diff_ref)
    agent_state_dict = dashboard.agent_state

    if not agent_state_dict:
        from harness.copilot.agent_state import AgentState
        agent_state_dict = AgentState().to_dict()

    # Convert dict back to AgentState for the renderer
    from harness.copilot.agent_state import AgentState as AS
    astate = AS(
        state=agent_state_dict.get("state", "idle"),
        confidence=agent_state_dict.get("confidence", 0.0),
        source_events=agent_state_dict.get("source_events", []),
        summary=agent_state_dict.get("summary", ""),
        recommended_action=agent_state_dict.get("recommended_action", ""),
        severity=agent_state_dict.get("severity", "low"),
        blocking=agent_state_dict.get("blocking", False),
        timestamp=agent_state_dict.get("timestamp", ""),
    )

    print(render_agent_state(astate, format=args.format))


def cmd_agent_state_from_loop(args: argparse.Namespace) -> None:
    """Show inferred agent lifecycle state from a loop run directory."""
    from harness.copilot.agent_state.inference import infer_from_loop_artifacts
    from harness.copilot.agent_state.renderer import render_agent_state
    from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts

    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    artifacts = load_loop_artifacts(run_dir)
    astate = infer_from_loop_artifacts(artifacts)
    print(render_agent_state(astate, format=args.format))


# =================== Phase 7: PR/MR Integration Lite Commands ====================


def cmd_pr_pack(args: argparse.Namespace) -> None:
    """Export local PR review pack for a project."""
    from harness.copilot.pr_integration.pr_pack import build_pr_pack, export_pr_pack

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.abspath(args.out) if args.out else os.path.join(project_root, ".harness", "pr_pack")
    pack = build_pr_pack(project_root, diff_ref=args.diff_ref)
    result = export_pr_pack(pack, out_dir)

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ PR pack exported to: {out_dir}")
    print(f"   文件数: {len(result['files'])}")
    for fp in result["files"]:
        print(f"   - {fp}")


def cmd_pr_pack_from_loop(args: argparse.Namespace) -> None:
    """Export local PR review pack from a loop run directory."""
    from harness.copilot.pr_integration.pr_pack import build_pr_pack_from_loop, export_pr_pack

    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.abspath(args.out) if args.out else os.path.join(run_dir, "..", "..", "pr_pack")
    out_dir = os.path.abspath(out_dir)
    pack = build_pr_pack_from_loop(run_dir)
    result = export_pr_pack(pack, out_dir)

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Loop PR pack exported to: {out_dir}")
    print(f"   文件数: {len(result['files'])}")
    for fp in result["files"]:
        print(f"   - {fp}")


def cmd_loop_doctor(args: argparse.Namespace) -> None:
    """Detect installed tools and AI coding agents (Loop Installer)."""
    from harness.loop.discovery import detect_summary
    print(detect_summary())


def cmd_loop_suggest(args: argparse.Namespace) -> None:
    """Recommend loop topologies based on detected agents."""
    from harness.loop.discovery import detect_system
    from harness.loop.topology import suggest_summary
    sys_info = detect_system()
    print(suggest_summary(sys_info))


def cmd_loop_setup(args: argparse.Namespace) -> None:
    """Interactive or non-interactive loop setup."""
    from harness.loop.setup import setup_loop
    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)
    result = setup_loop(
        project_root,
        mode=args.mode,
        agents=args.agents.split(",") if args.agents else None,
        output_dir=args.out,
    )
    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown')}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ Loop configured at: {result['output_dir']}")
    print(f"   Mode: {result['mode']}")
    print(f"   Agents: {', '.join(result['agents'])}")
    print(f"   Config files: {len(result['config_files'])}")
    print(f"   Instruction files: {len(result['instruction_files'])}")


def cmd_loop_init(args: argparse.Namespace) -> None:
    """Non-interactive loop initialization."""
    from harness.loop.setup import init_loop
    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)
    result = init_loop(
        project_root,
        mode=args.mode,
        agents=args.agents.split(",") if args.agents else None,
        output_dir=args.out,
    )
    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown')}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ Loop initialized at: {result['output_dir']}")
    print(f"   Mode: {result['mode']}")
    print(f"   Agents: {', '.join(result['agents'])}")


def cmd_loop_run(args: argparse.Namespace) -> None:
    """Execute a configured loop cycle (MVP)."""
    from harness.loop.runner import run_loop
    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)
    result = run_loop(project_root, loop_dir=args.loop_dir)
    print(f"✅ Loop run completed: {result.get('run_dir', '(unknown)')}")
    print(f"   Steps: {len(result['steps'])}")
    print(f"   Worktree clean: {result.get('worktree_clean', False)}")


def cmd_pr_draft(args: argparse.Namespace) -> None:
    """Generate or create PR draft (v1.3.1)."""
    from harness.copilot.pr_draft import run_pr_draft

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    result = run_pr_draft(
        project_root,
        create=args.create,
        out_dir=args.out,
        base=args.base,
    )

    if not result.get("success"):
        if result.get("blocked"):
            print("❌ BLOCKED: Large files detected in diff:", file=sys.stderr)
            for f in result.get("blocked_files", []):
                print(f"   - {f}", file=sys.stderr)
            sys.exit(1)
        print(f"❌ Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    if args.create:
        print(f"✅ PR created: {result['url']}")
        return

    print(f"✅ PR draft generated at: {result['out_dir']}")
    print(f"   compare URL: {result.get('compare_url', 'N/A')}")
    print(f"   gh available: {result.get('gh_available', False)}")
    print(f"   gh authenticated: {result.get('gh_authenticated', False)}")
    if result.get("note"):
        print(f"   {result['note']}")


def cmd_pr_comment(args: argparse.Namespace) -> None:
    """Generate PR comment text from a project."""
    from harness.copilot.pr_integration.pr_pack import build_pr_pack
    from harness.copilot.pr_integration.pr_comment_renderer import render_pr_comment

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    pack = build_pr_pack(project_root, diff_ref=args.diff_ref)
    print(render_pr_comment(pack, format=args.format))


def cmd_pr_comment_from_loop(args: argparse.Namespace) -> None:
    """Generate PR comment text from a loop run directory."""
    from harness.copilot.pr_integration.pr_pack import build_pr_pack_from_loop
    from harness.copilot.pr_integration.pr_comment_renderer import render_pr_comment

    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    pack = build_pr_pack_from_loop(run_dir)
    print(render_pr_comment(pack, format=args.format))


# =================== Phase 8A: Live Event Stream Commands ====================


def cmd_live_events(args: argparse.Namespace) -> None:
    """Capture current project state as live event(s)."""
    from harness.copilot.live.project_stream import capture_project_live_events
    from harness.copilot.live.renderer import render_events_json

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    events = capture_project_live_events(project_root, diff_ref=args.diff_ref)
    print(render_events_json(events))


def cmd_live_events_from_loop(args: argparse.Namespace) -> None:
    """Capture current loop artifact state as live event(s)."""
    from harness.copilot.live.loop_stream import capture_loop_live_events
    from harness.copilot.live.renderer import render_events_json

    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    events = capture_loop_live_events(run_dir)
    print(render_events_json(events))


def cmd_live_server(args: argparse.Namespace) -> None:
    """Start local-only SSE live event server."""
    from harness.copilot.live.sse_server import serve

    host = args.host
    if host != "127.0.0.1":
        print("Warning: live-server is local-only. Forcing 127.0.0.1.", file=sys.stderr)
        host = "127.0.0.1"

    # Populate event bus with initial project state
    project_root = os.path.abspath(args.project_path)
    if os.path.isdir(project_root):
        from harness.copilot.live.project_stream import capture_project_live_events
        capture_project_live_events(project_root, bus=None)

    serve(host=host, port=args.port, once=args.once)


# =================== Phase 8B: Live Dashboard UI Commands ====================


def cmd_live_dashboard(args: argparse.Namespace) -> None:
    """Generate a live dashboard HTML page for a project."""
    from harness.copilot.live.live_dashboard import build_live_dashboard

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.abspath(args.out) if args.out else os.path.join(project_root, ".harness", "live_dashboard")
    result = build_live_dashboard(project_root, diff_ref=args.diff_ref, output_dir=out_dir)

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Live dashboard generated")
    print(f"   路径: file://{result['html_path']}")
    print(f"   JSON: {result['json_path']}")
    print(f"   输出目录: {result['output_dir']}")
    print(f"   初始事件数: {len(result.get('initial_state', {}).get('events', []))}")


def cmd_live_dashboard_from_loop(args: argparse.Namespace) -> None:
    """Generate a live dashboard HTML page from a loop run directory."""
    from harness.copilot.live.live_dashboard import build_live_dashboard_from_loop

    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.abspath(args.out) if args.out else os.path.join(run_dir, "..", "..", "live_dashboard")
    out_dir = os.path.abspath(out_dir)
    result = build_live_dashboard_from_loop(run_dir, output_dir=out_dir)

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Live loop dashboard generated")
    print(f"   路径: file://{result['html_path']}")
    print(f"   JSON: {result['json_path']}")
    print(f"   输出目录: {result['output_dir']}")


# =================== Provider Reliability Guard Commands ====================


def cmd_provider_status(args: argparse.Namespace) -> None:
    """Show provider reliability guard status."""
    from harness.copilot.provider_guard import (
        get_diagnosis_summary,
        is_provider_degraded,
        run_canary_check,
    )

    summary = get_diagnosis_summary()

    if args.check:
        print("🔄 Running canary check...", file=sys.stderr)
        success, detail, _ = run_canary_check()
        summary = get_diagnosis_summary()
        print(f"   {'✅' if success else '❌'} {detail}", file=sys.stderr)
        print(file=sys.stderr)

    state_icon = {
        "healthy": "✅",
        "degraded": "⚠️ ",
        "failed": "❌",
        "unknown": "❓",
    }.get(summary["provider_health_state"], "❓")

    print(f"{state_icon} Provider Reliability Guard Status")
    print(f"   State:                {summary['provider_health_state']}")
    print(f"   Model:                {summary['model'] or '(not set)'}")
    print(f"   Degraded:             {summary['degraded']}")
    print(f"   Can proceed to Phase: {summary['can_proceed_to_long_phase']}")
    print(f"")
    print(f"   Endpoint check:       {summary['endpoint_healthcheck']}")
    print(f"   Model inference:      {summary['model_inference_healthcheck']}")
    print(f"   Failure type:         {summary['failure_type']}")
    print(f"")
    print(f"   Consecutive failures: {summary['consecutive_failures']}")
    print(f"   Last check:           {summary['last_check_at'] or '(never)'}")
    print(f"   Last success:         {summary['last_success_at'] or '(never)'}")
    print(f"   Last failure:         {summary['last_failure_at'] or '(never)'}")
    if summary["last_failure_detail"]:
        print(f"   Last failure detail:  {summary['last_failure_detail']}")
    if summary["last_failure_has_http_status"]:
        print(f"   Last HTTP status:     {summary['last_failure_http_status']}")
    print(f"")
    print(f"   Guard config:")
    for k, v in summary["guard_config"].items():
        print(f"     {k}: {v}")

    if args.format == "json" or args.json:
        import json as _json
        print(_json.dumps(summary, indent=2, ensure_ascii=False))


# =================== Foundation: Config / Doctor / Version Commands ====================


def cmd_config_init(args: argparse.Namespace) -> None:
    """Initialize global config file at ~/.harness/config.yaml."""
    from harness.config.loader import write_default_global_config
    force = getattr(args, "force", False)
    try:
        path = write_default_global_config(force=force)
        print(f"✅ Config initialized: {path}")
    except FileExistsError as e:
        print(f"⚠️  {e}")
        print("   Use --force to overwrite.")
        sys.exit(1)


def cmd_config_show(args: argparse.Namespace) -> None:
    """Show effective (merged) configuration."""
    from harness.config.resolver import resolve_config
    import json
    cfg = resolve_config(
        project_root=getattr(args, "project", None),
    )
    print(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False))


def cmd_config_path(args: argparse.Namespace) -> None:
    """Show config file paths."""
    from harness.config.paths import resolve_effective_paths
    paths = resolve_effective_paths(
        project_root=getattr(args, "project", None),
    )
    print(f"Global config: {paths['global_config_path']}")
    print(f"  Exists: {paths['global_config_exists']}")
    print(f"Project config: {paths['project_config_path']}")
    print(f"  Exists: {paths['project_config_exists']}")


def cmd_config_validate(args: argparse.Namespace) -> None:
    """Validate configuration for safety and completeness."""
    from harness.config.validator import validate_config
    result = validate_config(
        project_root=getattr(args, "project", None),
    )
    if result["errors"]:
        for err in result["errors"]:
            print(f"❌ ERROR: {err}")
    if result["warnings"]:
        for warn in result["warnings"]:
            print(f"⚠️  WARNING: {warn}")
    if result["info"]:
        for info in result["info"]:
            print(f"ℹ️  {info}")
    if result["security_issues"]:
        print("")
        for si in result["security_issues"]:
            print(f"🔒 {si}")
    print("")
    if result["valid"]:
        print("✅ Configuration is valid.")
    else:
        print("❌ Configuration has errors.")
        sys.exit(1)


def cmd_doctor(args: argparse.Namespace) -> None:
    """Run runtime doctor checks."""
    from harness.runtime.doctor import run_doctor, doctor_summary
    results = run_doctor()
    print("\n" + doctor_summary(results))


def cmd_version(args: argparse.Namespace) -> None:
    """Show Harness Copilot version."""
    from harness.runtime.version import get_version_info, format_version
    info = get_version_info()
    print(format_version(info))
    if args.json:
        import json as _json
        print(_json.dumps(info, indent=2))


# =================== Phase 5: Monitor Commands ====================


def cmd_monitor(args: argparse.Namespace) -> None:
    """Start project file monitoring."""
    from harness.copilot.monitor import MonitorEvent, MonitorSession
    from harness.copilot.monitor.watcher import ProjectWatcher
    from harness.copilot.monitor.terminal_renderer import (
        render_startup_message,
        render_event,
        render_status_line,
        render_agent_status,
    )
    from harness.copilot.monitor.dashboard_refresher import refresh_dashboard

    project_root = os.path.abspath(args.project_path)
    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    interval = args.interval
    out_dir = os.path.abspath(args.out) if args.out else None

    def on_event(event: MonitorEvent) -> None:
        print(render_event(event))
        # Show agent state after each event
        if watcher.session:
            print(f"  {render_agent_status(watcher.session)}")
        # Optionally refresh dashboard
        if out_dir and watcher.session:
            refresh_dashboard(out_dir, watcher.session, project_root=project_root)

    watcher = ProjectWatcher(project_root, interval=interval, on_event=on_event)

    print(render_startup_message(project_root, interval))
    print()

    try:
        watcher.run(max_polls=1 if getattr(args, 'once', False) else None)
    except KeyboardInterrupt:
        print(f"\n  {render_status_line(watcher.session)}")
        if watcher.session:
            print(f"  {render_agent_status(watcher.session)}")
        print("  监控已停止。")

    if out_dir:
        result = refresh_dashboard(out_dir, watcher.session, project_root=project_root)
        if result.get("success"):
            print(f"  Dashboard: file://{result.get('state_path', '')}", file=sys.stderr)


def cmd_monitor_loop(args: argparse.Namespace) -> None:
    """Start loop artifact monitoring."""
    from harness.copilot.monitor.watcher import LoopWatcher
    from harness.copilot.monitor.terminal_renderer import (
        render_startup_message,
        render_event,
        render_status_line,
        render_agent_status,
    )
    from harness.copilot.monitor.dashboard_refresher import refresh_dashboard

    run_dir = os.path.abspath(args.loop_run_dir)
    if not os.path.isdir(run_dir):
        print(f"Error: '{run_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    interval = args.interval
    out_dir = os.path.abspath(args.out) if args.out else None

    def on_event(event) -> None:
        print(render_event(event))
        # Show agent state after each event
        if watcher.session:
            print(f"  {render_agent_status(watcher.session)}")
        if out_dir and watcher.session:
            refresh_dashboard(out_dir, watcher.session, loop_run_dir=run_dir)

    watcher = LoopWatcher(run_dir, interval=interval, on_event=on_event)

    print(render_startup_message(run_dir, interval))
    print()

    try:
        watcher.run(max_polls=1 if getattr(args, 'once', False) else None)
    except KeyboardInterrupt:
        print(f"\n  {render_status_line(watcher.session)}")
        if watcher.session:
            print(f"  {render_agent_status(watcher.session)}")
        print("  监控已停止。")

    if out_dir:
        result = refresh_dashboard(out_dir, watcher.session, loop_run_dir=run_dir)
        if result.get("success"):
            print(f"  Dashboard: {result.get('state_path', '')}", file=sys.stderr)


# =================== Main ====================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Harness Code Copilot — AI Coding Semantic Copilot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--json", action="store_true", help="Output full JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect project structure")
    p_inspect.add_argument("project_path", help="Path to project root")
    p_inspect.set_defaults(func=cmd_inspect)

    # diff-summary
    p_diff = subparsers.add_parser("diff-summary", help="Summarize recent changes")
    p_diff.add_argument("project_path", help="Path to project root")
    p_diff.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_diff.add_argument("--quick", "-q", action="store_true", help="Quick text summary")
    p_diff.set_defaults(func=cmd_diff_summary)

    # task-card
    p_card = subparsers.add_parser("task-card", help="Generate task cards")
    p_card.add_argument("project_path", help="Path to project root")
    p_card.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_card.set_defaults(func=cmd_task_card)

    # readiness
    p_readiness = subparsers.add_parser("readiness", help="Evaluate merge readiness")
    p_readiness.add_argument("project_path", help="Path to project root")
    p_readiness.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_readiness.set_defaults(func=cmd_readiness)

    # ==================== UX Layer Commands ====================

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Full project dashboard (UX)")
    p_dash.add_argument("project_path", help="Path to project root")
    p_dash.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_dash.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")
    p_dash.set_defaults(func=cmd_dashboard)

    # modules
    p_mod = subparsers.add_parser("modules", help="Module cards (UX)")
    p_mod.add_argument("project_path", help="Path to project root")
    p_mod.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_mod.add_argument("--format", choices=["markdown", "json"], default="markdown",
                       help="Output format (default: markdown)")
    p_mod.set_defaults(func=cmd_ux_modules)

    # task-cards
    p_tc = subparsers.add_parser("task-cards", help="Task cards (UX)")
    p_tc.add_argument("project_path", help="Path to project root")
    p_tc.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_tc.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
    p_tc.set_defaults(func=cmd_ux_task_cards)

    # ==================== Integration Layer Commands ====================

    # from-loop
    p_fl = subparsers.add_parser("from-loop", help="Dashboard from loop artifacts (Integration)")
    p_fl.add_argument("loop_run_dir", help="Path to loop run directory")
    p_fl.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
    p_fl.set_defaults(func=cmd_from_loop)

    # evidence
    p_ev = subparsers.add_parser("evidence", help="Evidence pack from loop (Integration)")
    p_ev.add_argument("loop_run_dir", help="Path to loop run directory")
    p_ev.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
    p_ev.set_defaults(func=cmd_evidence)

    # repair-cards
    p_rc = subparsers.add_parser("repair-cards", help="Repair task cards from loop (Integration)")
    p_rc.add_argument("loop_run_dir", help="Path to loop run directory")
    p_rc.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
    p_rc.set_defaults(func=cmd_repair_cards)

    # ==================== Phase 4: MVP Shell Commands ====================

    # shell
    p_shell = subparsers.add_parser("shell", help="Generate static HTML dashboard (Phase 4)")
    p_shell.add_argument("project_path", help="Path to project root")
    p_shell.add_argument("--out", "-o", default=None, help="Output directory")
    p_shell.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_shell.set_defaults(func=cmd_shell)

    # shell-from-loop
    p_sfl = subparsers.add_parser("shell-from-loop", help="Generate HTML dashboard from loop artifacts (Phase 4)")
    p_sfl.add_argument("loop_run_dir", help="Path to loop run directory")
    p_sfl.add_argument("--out", "-o", default=None, help="Output directory")
    p_sfl.set_defaults(func=cmd_shell_from_loop)

    # export-task-card
    p_etc = subparsers.add_parser("export-task-card", help="Export task card as markdown (Phase 4)")
    p_etc.add_argument("project_path", help="Path to project root")
    p_etc.add_argument("--out", "-o", default=None, help="Output file path")
    p_etc.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_etc.add_argument("--card-index", type=int, default=None, help="Export single card by index (0-based)")
    p_etc.set_defaults(func=cmd_export_task_card)

    # preview
    p_preview = subparsers.add_parser("preview", help="Start local read-only preview server (Phase 4)")
    p_preview.add_argument("dashboard_dir", help="Path to dashboard output directory")
    p_preview.add_argument("--port", type=int, default=8080, help="Local port (default: 8080)")
    p_preview.set_defaults(func=cmd_preview)

    # ==================== Phase 6B: Agent State Commands ====================

    # agent-state
    p_as = subparsers.add_parser("agent-state", help="Show inferred agent lifecycle state (Phase 6B)")
    p_as.add_argument("project_path", help="Path to project root")
    p_as.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_as.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
    p_as.set_defaults(func=cmd_agent_state)

    # agent-state-from-loop
    p_asfl = subparsers.add_parser("agent-state-from-loop", help="Show agent state from loop artifacts (Phase 6B)")
    p_asfl.add_argument("loop_run_dir", help="Path to loop run directory")
    p_asfl.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")
    p_asfl.set_defaults(func=cmd_agent_state_from_loop)

    # ==================== Phase 7: PR/MR Integration Commands ====================

    # pr-pack
    p_pp = subparsers.add_parser("pr-pack", help="Export local PR review pack (Phase 7)")
    p_pp.add_argument("project_path", help="Path to project root")
    p_pp.add_argument("--out", "-o", default=None, help="Output directory")
    p_pp.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_pp.set_defaults(func=cmd_pr_pack)

    # pr-pack-from-loop
    p_ppfl = subparsers.add_parser("pr-pack-from-loop", help="Export PR pack from loop artifacts (Phase 7)")
    p_ppfl.add_argument("loop_run_dir", help="Path to loop run directory")
    p_ppfl.add_argument("--out", "-o", default=None, help="Output directory")
    p_ppfl.set_defaults(func=cmd_pr_pack_from_loop)

    # pr-comment
    p_pc = subparsers.add_parser("pr-comment", help="Generate PR comment markdown (Phase 7)")
    p_pc.add_argument("project_path", help="Path to project root")
    p_pc.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_pc.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
    p_pc.set_defaults(func=cmd_pr_comment)

    # pr-comment-from-loop
    p_pcfl = subparsers.add_parser("pr-comment-from-loop", help="Generate PR comment from loop artifacts (Phase 7)")
    p_pcfl.add_argument("loop_run_dir", help="Path to loop run directory")
    p_pcfl.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")
    p_pcfl.set_defaults(func=cmd_pr_comment_from_loop)

    # pr-draft (v1.3.1)
    p_pd = subparsers.add_parser("pr-draft", help="Generate or create PR draft (v1.3.1)")
    p_pd.add_argument("project_path", help="Path to project root")
    p_pd.add_argument("--out", "-o", default=None, help="Output directory for draft pack")
    p_pd.add_argument("--create", action="store_true", help="Create PR via gh CLI")
    p_pd.add_argument("--base", default=None, help="Base branch (default: auto-detect main/master)")
    p_pd.set_defaults(func=cmd_pr_draft)

    # ==================== Phase 8A: Live Event Stream Commands ====================

    # live-events
    p_le = subparsers.add_parser("live-events", help="Capture project live events (Phase 8A)")
    p_le.add_argument("project_path", help="Path to project root")
    p_le.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_le.set_defaults(func=cmd_live_events)

    # live-events-from-loop
    p_lefl = subparsers.add_parser("live-events-from-loop", help="Capture loop live events (Phase 8A)")
    p_lefl.add_argument("loop_run_dir", help="Path to loop run directory")
    p_lefl.set_defaults(func=cmd_live_events_from_loop)

    # live-server
    p_ls = subparsers.add_parser("live-server", help="Start local SSE live event server (Phase 8A)")
    p_ls.add_argument("project_path", help="Path to project root")
    p_ls.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    p_ls.add_argument("--port", type=int, default=8765, help="Listen port (default: 8765)")
    p_ls.add_argument("--once", action="store_true", help="Handle one request then exit")
    p_ls.set_defaults(func=cmd_live_server)

    # ==================== Phase 8B: Live Dashboard UI Commands ====================

    # live-dashboard
    p_ld = subparsers.add_parser("live-dashboard", help="Generate live dashboard HTML (Phase 8B)")
    p_ld.add_argument("project_path", help="Path to project root")
    p_ld.add_argument("--out", "-o", default=None, help="Output directory")
    p_ld.add_argument("--diff-ref", default="HEAD~1", help="Git diff base ref")
    p_ld.set_defaults(func=cmd_live_dashboard)

    # live-dashboard-from-loop
    p_ldfl = subparsers.add_parser("live-dashboard-from-loop", help="Generate live dashboard from loop (Phase 8B)")
    p_ldfl.add_argument("loop_run_dir", help="Path to loop run directory")
    p_ldfl.add_argument("--out", "-o", default=None, help="Output directory")
    p_ldfl.set_defaults(func=cmd_live_dashboard_from_loop)

    # Provider Reliability Guard
    p_ps = subparsers.add_parser("provider-status", help="Show provider reliability guard status")
    p_ps.add_argument("--check", action="store_true", help="Force a canary check")
    p_ps.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
    p_ps.set_defaults(func=cmd_provider_status)

    # ==================== Loop Installer Commands (v1.4) ====================

    # loop doctor
    p_ld_doc = subparsers.add_parser("loop", help="Manage loop installer")
    p_ld_sub = p_ld_doc.add_subparsers(dest="loop_command", help="Loop sub-command")

    p_ld_doc_cmd = p_ld_sub.add_parser("doctor", help="Detect installed tools and AI agents")
    p_ld_doc_cmd.set_defaults(func=cmd_loop_doctor)

    p_ld_sug = p_ld_sub.add_parser("suggest", help="Recommend loop topologies")
    p_ld_sug.set_defaults(func=cmd_loop_suggest)

    p_ld_setup = p_ld_sub.add_parser("setup",
        help="Configure loop (interactive or non-interactive)")
    p_ld_setup.add_argument("project_path", help="Path to project root")
    p_ld_setup.add_argument("--mode", choices=["single_agent", "multi_agent"],
                            default="single_agent", help="Loop mode")
    p_ld_setup.add_argument("--agents", default=None, help="Comma-separated agent list")
    p_ld_setup.add_argument("--out", "-o", default=None, help="Output directory")
    p_ld_setup.set_defaults(func=cmd_loop_setup)

    p_ld_init = p_ld_sub.add_parser("init", help="Initialize loop (non-interactive)")
    p_ld_init.add_argument("project_path", help="Path to project root")
    p_ld_init.add_argument("--mode", choices=["single_agent", "multi_agent"],
                           default="single_agent", help="Loop mode")
    p_ld_init.add_argument("--agents", default=None, help="Comma-separated agent list")
    p_ld_init.add_argument("--out", "-o", default=None, help="Output directory")
    p_ld_init.set_defaults(func=cmd_loop_init)

    p_ld_run = p_ld_sub.add_parser("run", help="Execute a loop cycle (MVP)")
    p_ld_run.add_argument("project_path", help="Path to project root")
    p_ld_run.add_argument("--loop-dir", default=None, help="Loop config directory")
    p_ld_run.set_defaults(func=cmd_loop_run)

    # Foundation: Config / Doctor / Version
    p_cfg_init = subparsers.add_parser("config", help="Manage configuration")
    p_cfg_sub = p_cfg_init.add_subparsers(dest="config_command", help="Config sub-command")

    p_cfg_init_cmd = p_cfg_sub.add_parser("init", help="Initialize global config")
    p_cfg_init_cmd.add_argument("--force", action="store_true", help="Overwrite existing config")
    p_cfg_init_cmd.set_defaults(func=cmd_config_init)

    p_cfg_show = p_cfg_sub.add_parser("show", help="Show effective configuration")
    p_cfg_show.add_argument("--project", default=None, help="Project root path")
    p_cfg_show.set_defaults(func=cmd_config_show)

    p_cfg_path = p_cfg_sub.add_parser("path", help="Show config file paths")
    p_cfg_path.add_argument("--project", default=None, help="Project root path")
    p_cfg_path.set_defaults(func=cmd_config_path)

    p_cfg_val = p_cfg_sub.add_parser("validate", help="Validate configuration")
    p_cfg_val.add_argument("--project", default=None, help="Project root path")
    p_cfg_val.set_defaults(func=cmd_config_validate)

    p_doc = subparsers.add_parser("doctor", help="Run runtime doctor checks")
    p_doc.set_defaults(func=cmd_doctor)

    p_ver = subparsers.add_parser("version", help="Show version info")
    p_ver.add_argument("--json", action="store_true", help="Output JSON")
    p_ver.set_defaults(func=cmd_version)

    # ==================== Phase 5: Monitor Commands ====================

    # monitor
    p_mon = subparsers.add_parser("monitor", help="Start project file monitoring (Phase 5)")
    p_mon.add_argument("project_path", help="Path to project root")
    p_mon.add_argument("--interval", type=float, default=3.0, help="Poll interval in seconds (default: 3)")
    p_mon.add_argument("--out", "-o", default=None, help="Dashboard output directory (optional)")
    p_mon.add_argument("--once", action="store_true", help="Single poll then exit (for smoke test)")
    p_mon.set_defaults(func=cmd_monitor)

    # monitor-loop
    p_ml = subparsers.add_parser("monitor-loop", help="Start loop artifact monitoring (Phase 5)")
    p_ml.add_argument("loop_run_dir", help="Path to loop run directory")
    p_ml.add_argument("--interval", type=float, default=3.0, help="Poll interval in seconds (default: 3)")
    p_ml.add_argument("--out", "-o", default=None, help="Dashboard output directory (optional)")
    p_ml.add_argument("--once", action="store_true", help="Single poll then exit (for smoke test)")
    p_ml.set_defaults(func=cmd_monitor_loop)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle config subcommand dispatch
    if args.command == "config" and not getattr(args, "config_command", None):
        p_cfg_init.print_help()
        sys.exit(1)

    # Handle loop subcommand dispatch
    if args.command == "loop" and not getattr(args, "loop_command", None):
        p_ld_doc.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
