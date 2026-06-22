#!/usr/bin/env python3
"""Harness Code Copilot — Thin CLI Skeleton.

Usage:
  harness copilot inspect <project_path>
  harness copilot diff-summary <project_path> [--diff-ref=<ref>]
  harness copilot task-card <project_path> [--diff-ref=<ref>]
  harness copilot readiness <project_path> [--diff-ref=<ref>]

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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
