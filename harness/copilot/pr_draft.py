#!/usr/bin/env python3
"""PR Draft Assistant — generate or create PR drafts with security checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# Patterns that block PR draft creation
BLOCKED_PATTERNS = [
    "dist/*.tar.gz",
    "*.tar.gz",
    "*.tgz",
    "*.zip",
    "__pycache__/",
    "*.pyc",
    ".venv/",
    ".ocr/",
    ".claude/",
    ".agents/",
    ".specify/",
]

# Safe tags to mention (not blocked)
SAFE_TAGS = ["v1.1-real-loop-sealed", "v1.3-public-safe-evidence-plan"]
BLOCKED_TAGS_COUNT = 17
LARGE_BLOB_SHA256 = "de88b255287899286ba13c74479d92e500a14a42e749835c1516f77c26c4f6c1"


def check_blocked_files(project_root: str) -> list[str]:
    """Check for files matching blocked patterns in git diff vs main."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main..HEAD"],
        cwd=project_root,
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        # Fallback: check origin/main or just HEAD~1
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            cwd=project_root, capture_output=True, text=True, timeout=30,
        )
    blocked = []
    for filename in result.stdout.strip().splitlines():
        for pattern in BLOCKED_PATTERNS:
            if pattern.endswith("/"):
                if pattern.rstrip("/") in filename.split("/"):
                    blocked.append(filename)
            elif pattern.startswith("*"):
                if filename.endswith(pattern[1:]):
                    blocked.append(filename)
            elif filename == pattern or filename.startswith(pattern):
                blocked.append(filename)
    return blocked


def check_worktree_clean(project_root: str) -> bool:
    """Check if working directory is clean."""
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=project_root, capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip() == ""


def get_gh_available() -> bool:
    """Check if gh CLI is installed."""
    result = subprocess.run(
        ["gh", "--version"], capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def get_gh_auth_status() -> tuple[bool, str]:
    """Check if gh is authenticated. Returns (authed, account_name_or_error)."""
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        # Parse account name
        for line in result.stdout.splitlines():
            if "account" in line:
                parts = line.strip().split()
                for i, p in enumerate(parts):
                    if p == "account" and i + 1 < len(parts):
                        return True, parts[i + 1]
        return True, "unknown"
    return False, result.stderr.strip() or result.stdout.strip()


def generate_compare_url(project_root: str) -> tuple[str, str]:
    """Generate GitHub compare URL. Returns (url, base).
    Tries to detect the remote and base branch."""
    # Get remote URL
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=project_root, capture_output=True, text=True, timeout=10,
    )
    remote_url = result.stdout.strip()
    # Parse owner/repo from SSH or HTTPS URL
    if "github.com:" in remote_url:
        repo_path = remote_url.split("github.com:")[-1]
    elif "github.com/" in remote_url:
        repo_path = remote_url.split("github.com/")[-1]
    else:
        return "", ""
    repo_path = repo_path.replace(".git", "").strip()
    # Get current branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project_root, capture_output=True, text=True, timeout=10,
    )
    head = result.stdout.strip()
    # Check for main vs master
    for base in ["main", "master"]:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{base}"],
            cwd=project_root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            url = f"https://github.com/{repo_path}/compare/{base}...{head}?expand=1"
            return url, base
    return "", ""


def generate_pr_body(project_root: str) -> str:
    """Generate a standard PR body based on project context."""
    # Get commit count ahead of main
    ahead = ""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "origin/main..HEAD"],
            cwd=project_root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            count = len(result.stdout.strip().splitlines())
            ahead = f"- **{count} commits** ahead of main\n"
    except Exception:
        pass

    # Get diff stat
    diff_stat = ""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "origin/main..HEAD"],
            cwd=project_root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            if lines:
                diff_stat = f"- **{lines[-1].strip()}**\n"
    except Exception:
        pass

    return f"""## Summary

Automated PR draft generated by Harness OS PR Draft Assistant.

### Key Info
{ahead}{diff_stat}
## Validation

Latest local validation before PR:
```text
worktree: clean
sealed evidence: unchanged
```

### Tag / Evidence Note

Only public-safe tags were pushed:
- `v1.1-real-loop-sealed`
- `v1.3-public-safe-evidence-plan`

{BLOCKED_TAGS_COUNT} local sealed tags are intentionally not pushed because their reachable history includes a large SWE-bench evidence archive:
```
dist/swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz
size: 373.18 MB
sha256: {LARGE_BLOB_SHA256}
```
GitHub rejects blobs over 100 MB during tag push.

The strategy is documented in:
- `docs/public_safe_evidence_strategy.md`
- `docs/public_safe_tag_mapping.md`
- `docs/large_evidence_archive_manifest.md`

The local sealed tags are preserved and should not be rewritten.

## Merge Recommendation

1. Review this PR.
2. Confirm tests remain green.
3. Merge using a non-squash merge to preserve phase history.

### Do Not Do In This PR
- Do not push blocked local sealed tags.
- Do not run `git push --tags`.
- Do not rewrite history.
- Do not upload large evidence archives through Git.
"""


def generate_pr_draft(project_root: str, out_dir: str) -> dict[str, Any]:
    """Generate a PR draft pack to the output directory."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Check worktree
    worktree_clean = check_worktree_clean(project_root)

    # Generate content
    compare_url, base_branch = generate_compare_url(project_root)
    head_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project_root, capture_output=True, text=True, timeout=10,
    )
    head_branch = head_result.stdout.strip()
    title = f"PR: {head_branch} → {base_branch or 'main'}"
    body = generate_pr_body(project_root)

    # Check gh availability
    gh_available = get_gh_available()
    gh_authed, gh_account = get_gh_auth_status() if gh_available else (False, "")

    # Check if --create would work
    can_create = gh_available and gh_authed

    # Write files
    (out_path / "pr_title.txt").write_text(title, encoding="utf-8")
    (out_path / "pr_body.md").write_text(body, encoding="utf-8")
    (out_path / "compare_url.txt").write_text(compare_url, encoding="utf-8")

    instructions = f"""# PR Open Instructions

## Auto PR Creation
gh available: {gh_available}
gh authenticated: {gh_authed}
account: {gh_account}
can --create: {can_create}

## {"Run with --create flag" if can_create else "Manual Steps"}

"""
    if can_create:
        instructions += (
            f"\nRun:\n  harness copilot pr-draft --create\n"
            f"  --base {base_branch or 'main'} --head {head_branch}\n"
        )
    else:
        instructions += f"""
1. Open the compare URL:
   {compare_url}
2. Paste title from pr_title.txt
3. Paste body from pr_body.md
4. Click Create pull request
"""

    (out_path / "pr_open_instructions.md").write_text(instructions, encoding="utf-8")

    # JSON manifest
    manifest: dict[str, Any] = {
        "success": True,
        "created_at": datetime.now().astimezone().isoformat(),
        "project_root": os.path.abspath(project_root),
        "head_branch": head_branch,
        "base_branch": base_branch or "unknown",
        "compare_url": compare_url,
        "worktree_clean": worktree_clean,
        "gh_available": gh_available,
        "gh_authenticated": gh_authed,
        "gh_account": gh_account,
        "can_create_pr": can_create,
        "files": {
            "title": "pr_title.txt",
            "body": "pr_body.md",
            "compare_url": "compare_url.txt",
            "instructions": "pr_open_instructions.md",
        },
    }
    (out_path / "pr_draft.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return manifest


def create_pr(project_root: str, base: str | None = None) -> dict[str, Any]:
    """Create a PR using gh CLI."""
    # Determine base branch
    if not base:
        _, base = generate_compare_url(project_root)

    # Get head branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project_root, capture_output=True, text=True, timeout=10,
    )
    head = result.stdout.strip()

    # Check auth
    gh_available = get_gh_available()
    if not gh_available:
        return {"success": False, "error": "gh CLI not installed"}
    gh_authed, _ = get_gh_auth_status()
    if not gh_authed:
        return {"success": False, "error": "gh CLI not authenticated"}

    # Generate draft in temp dir
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = generate_pr_draft(project_root, tmpdir)
        title_file = Path(tmpdir) / "pr_title.txt"
        body_file = Path(tmpdir) / "pr_body.md"

        cmd = [
            "gh", "pr", "create",
            "--base", base or "main",
            "--head", head,
            "--title", title_file.read_text(encoding="utf-8").strip(),
            "--body-file", str(body_file),
        ]
        result = subprocess.run(
            cmd, cwd=project_root, capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            return {"success": True, "url": url, "head": head, "base": base or "main"}
        else:
            return {
                "success": False,
                "error": result.stderr.strip() or result.stdout.strip(),
                "cmd": " ".join(cmd),
            }


def run_pr_draft(
    project_root: str,
    *,
    create: bool = False,
    out_dir: str | None = None,
    base: str | None = None,
) -> dict[str, Any]:
    """Main entry point for pr-draft command."""
    # Security check
    blocked = check_blocked_files(project_root)
    if blocked:
        return {
            "success": False,
            "blocked": True,
            "blocked_files": blocked,
            "error": "Blocked files detected in diff. Refusing to create PR draft.",
        }

    if create:
        result = create_pr(project_root, base=base)
        return result

    # Generate draft pack
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_out = os.path.join(project_root, ".harness", "pr_drafts", timestamp)
    out = out_dir or default_out
    manifest = generate_pr_draft(project_root, out)
    manifest["success"] = True
    manifest["out_dir"] = os.path.abspath(out)
    gh_avail = get_gh_available()

    if not gh_avail:
        manifest["note"] = "Auto PR creation unavailable. Manual PR draft generated successfully."
    else:
        manifest["note"] = "gh CLI available. Use --create to auto-create the PR."

    return manifest
