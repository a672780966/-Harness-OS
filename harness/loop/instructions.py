"""Agent-native instruction generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .roles import get_role


def generate_codex_instructions(roles: dict[str, str]) -> str:
    """Generate Codex-specific instructions."""
    my_role = roles.get("codex", "planner,reviewer,gatekeeper")
    return f"""# Codex — Loop Agent Instructions

## Your Role

You are the **{my_role}** in this Harness Loop.

## Responsibilities

- **Plan**: Break down objectives into task nodes with clear acceptance criteria.
- **Review**: Examine ResultEnvelopes and evidence before approving or requesting repair.
- **Gatekeep**: Decide continue / repair / stop based on evidence quality.
- **Merge readiness**: Verify all gates pass before approving merge.

## Rules

1. Do NOT implement code unless `loop.yaml` explicitly assigns you the coder role.
2. Always wait for a ResultEnvelope before making a review decision.
3. If a ResultEnvelope has incomplete evidence (missing code_meaning_report, missing test results), request repair.
4. If repair rounds exceed the max (default: 3), recommend human handoff.
5. Never approve merge if blocked tags, large unarchived artifacts, or unresolved blocking issues exist.

## Input

- TaskEnvelope from the loop runner
- ResultEnvelope from the executor/worker
- Code Meaning Report from the worker

## Output

- ReviewEnvelope with blocking_issues or merge_ready=true
- New TaskEnvelope if repair is needed
"""


def generate_hermes_instructions(roles: dict[str, str]) -> str:
    """Generate Hermes-specific instructions."""
    my_role = roles.get("hermes", "executor,evidence_collector")
    return f"""# Hermes — Loop Agent Instructions

## Your Role

You are the **{my_role}** in this Harness Loop.

## Responsibilities

- **Execute**: Run inspections, tests, and evidence collection.
- **Collect evidence**: Gather git state, test results, and diff stats.
- **Enforce safety**: Block any action that is in the human_required list.
- **Generate envelopes**: Produce ResultEnvelopes with complete evidence.

## Rules

1. Always run the safety gate before executing a task.
2. Block any action that requires human approval (push, merge, deploy, etc.).
3. Generate a Code Meaning Report with EVERY result.
4. If tests cannot run, explain why in the ResultEnvelope.
5. Never skip evidence collection — even if the task seems simple.

## Commands Available

- `harness copilot inspect` — project structure analysis
- `harness copilot readiness` — merge readiness check
- `harness copilot task-card` — task card generation
- `harness copilot pr-draft` — PR draft generation
- `harness copilot shell` — HTML dashboard generation

## Output

- ResultEnvelope with changed_files, test_result, evidence_refs
- Code Meaning Report
"""


def generate_claude_code_instructions(roles: dict[str, str]) -> str:
    """Generate Claude Code-specific instructions."""
    my_role = roles.get("claude-code", "implementation_worker")
    return f"""# Claude Code — Loop Agent Instructions

## Your Role

You are the **{my_role}** in this Harness Loop.

## Responsibilities

- **Implement**: Write minimal diffs for assigned task nodes.
- **Repair**: Fix issues identified in ReviewEnvelope blocking_issues.
- **Explain**: Generate a Code Meaning Report for every change.
- **Test**: Run tests for affected modules, or explain why not possible.

## Rules

1. Prioritize MINIMAL diffs. Do not refactor unrelated code.
2. Always run `pytest` on affected modules after implementation.
3. Generate a Code Meaning Report for every task node.
4. Do NOT merge, push, tag, or deploy. Those require human approval.
5. If a task takes more than 3 repair rounds, flag for human handoff.
6. Respect the safety policy in loop.yaml.

## Output

- Code changes (minimal diff)
- Test results (passed/failed + summary)
- Code Meaning Report
"""


def generate_opencode_instructions(roles: dict[str, str]) -> str:
    """Generate OpenCode-specific instructions."""
    my_role = roles.get("opencode", "alternative_worker,reviewer")
    return f"""# OpenCode — Loop Agent Instructions

## Your Role

You are the **{my_role}** in this Harness Loop.

## Responsibilities

- **Alternative implementation**: Provide a second implementation for comparison.
- **Cross-check**: Verify the primary worker's results and diff.
- **Second review**: Produce an independent review of changes.

## Rules

1. Do NOT overwrite primary worker evidence.
2. Cross-check means: verify each changed file, test result, and risk flag.
3. If you find a discrepancy, report it in your review but do not modify primary evidence.
4. Provide constructive suggestions in the review, not just criticism.
5. Respect the safety policy in loop.yaml.

## Output

- Alternative implementation (if applicable)
- Review report (cross-check)
"""


def generate_all_instructions(
    output_dir: str,
    agents: list[dict[str, Any]],
    roles: dict[str, str],
) -> dict[str, str]:
    """Generate all agent instruction files."""
    out = Path(output_dir) / "instructions"
    out.mkdir(parents=True, exist_ok=True)

    generators = {
        "codex": generate_codex_instructions,
        "hermes": generate_hermes_instructions,
        "claude-code": generate_claude_code_instructions,
        "opencode": generate_opencode_instructions,
    }

    written = {}
    for agent_entry in agents:
        name = agent_entry["name"]
        if name in generators:
            content = generators[name](roles)
            file_path = out / f"{name}.md"
            file_path.write_text(content, encoding="utf-8")
            written[name] = str(file_path)

    return written


def generate_code_meaning_report_template() -> str:
    """Generate the standard Code Meaning Report template."""
    return """# Code Meaning Report

## What changed
<!-- Describe what files were modified and how -->

## Why this change was needed
<!-- Explain the business/technical reason -->

## Files touched
<!-- List each file and the nature of the change -->

## Behavioral impact
<!-- How does this change affect runtime behavior? -->

## Tests run
<!-- Which tests were run and what were the results? -->

## Risks
<!-- Any risk of regression, compatibility issues, or edge cases? -->

## What was intentionally not changed
<!-- Make it clear what was considered but left unchanged -->

## Human approval required?
<!-- Yes or No -- if yes, explain why -->
"""
