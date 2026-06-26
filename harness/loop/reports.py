"""Report generation for loop installer."""

from __future__ import annotations

from pathlib import Path


def generate_code_meaning_report(
    what_changed: str = "",
    why_changed: str = "",
    files_touched: str = "",
    behavioral_impact: str = "",
    tests_run: str = "",
    risks: str = "",
    intentionally_not_changed: str = "",
    human_approved_required: str = "",
) -> str:
    """Generate a Code Meaning Report."""
    return f"""# Code Meaning Report

## What changed
{what_changed or '_Describe what files were modified and how_'}

## Why this change was needed
{why_changed or '_Explain the business/technical reason_'}

## Files touched
{files_touched or '_List each file and the nature of the change_'}

## Behavioral impact
{behavioral_impact or '_How does this change affect runtime behavior?_'}

## Tests run
{tests_run or '_Which tests were run and what were the results?_'}

## Risks
{risks or '_Any risk of regression, compatibility issues, or edge cases?_'}

## What was intentionally not changed
{intentionally_not_changed or '_Make it clear what was considered but left unchanged_'}

## Human approval required?
{human_approved_required or '_Yes or No — if yes, explain why_'}
"""


def write_code_meaning_report(output_dir: str, **kwargs: str) -> str:
    """Write a Code Meaning Report to file."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    content = generate_code_meaning_report(**kwargs)
    path = out / "code_meaning_report.md"
    path.write_text(content, encoding="utf-8")
    return str(path)


def generate_handoff_file(agent_name: str, task_info: dict) -> str:
    """Generate a handoff file when no adapter is available."""
    return f"""# Handoff File for {agent_name}

## Agent Adapter Status

Adapter unavailable for {agent_name}. Generated handoff file.

## Task

- **Task ID**: {task_info.get('task_id', 'unknown')}
- **Objective**: {task_info.get('objective', 'unknown')}
- **Assigned Roles**: {task_info.get('roles', 'unknown')}

## Instructions

1. Review the task objective and acceptance criteria above.
2. Implement the required changes.
3. Run tests on affected modules.
4. Generate a Code Meaning Report (template below).
5. Provide a ResultEnvelope with your output.

## Code Meaning Report Template

```markdown
# Code Meaning Report
## What changed
## Why this change was needed
## Files touched
## Behavioral impact
## Tests run
## Risks
## What was intentionally not changed
## Human approval required?
```

## Safety Reminders

- Do NOT merge, push, tag, or deploy.
- Do NOT modify .env or secrets.
- Do NOT rewrite git history.
- Do NOT delete evidence.
"""


def write_handoff_file(output_dir: str, agent_name: str, task_info: dict) -> str:
    """Write a handoff file for an agent without an adapter."""
    out = Path(output_dir) / "handoffs"
    out.mkdir(parents=True, exist_ok=True)
    content = generate_handoff_file(agent_name, task_info)
    path = out / f"handoff_{agent_name}.md"
    path.write_text(content, encoding="utf-8")
    return str(path)
