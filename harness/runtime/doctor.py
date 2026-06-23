"""Runtime doctor — check system prerequisites for Harness Copilot.

Checks:
  - Python version (>= 3.10)
  - Git availability
  - pytest availability
  - OS detection (Linux, macOS, WSL2, Windows native)
  - WSL2 detection (on Windows)
  - Provider CLI availability (opencode)
  - Global config existence
  - .harness/runtime/ directory
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional


def _run(cmd: List[str], timeout: int = 5) -> Optional[str]:
    """Run a command and return stdout, or None on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _check_python() -> Dict[str, Any]:
    """Check Python runtime."""
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    return {
        "name": "python",
        "ok": ok,
        "detail": f"{sys.version}",
        "hint": "Required: Python >= 3.10" if not ok else "",
    }


def _check_git() -> Dict[str, Any]:
    """Check Git availability."""
    version = _run(["git", "--version"])
    ok = version is not None
    return {
        "name": "git",
        "ok": ok,
        "detail": version or "not found",
        "hint": "Install git (apt install git / brew install git)" if not ok else "",
    }


def _check_pytest() -> Dict[str, Any]:
    """Check pytest availability."""
    version = _run(["pytest", "--version"])
    ok = version is not None
    return {
        "name": "pytest",
        "ok": ok,
        "detail": version or "not found",
        "hint": "Install pytest (pip install pytest)" if not ok else "",
    }


def _check_os() -> Dict[str, Any]:
    """Detect operating system and WSL2."""
    system = platform.system()
    release = platform.release()
    machine = platform.machine()

    os_hint = "unknown"
    detail_parts = [f"{system} {machine}"]

    if system == "Linux":
        # Check for WSL2
        is_wsl = "microsoft" in release.lower() or "wsl" in release.lower()
        if is_wsl:
            os_hint = "wsl2"
            detail_parts.append("(WSL2)")
        else:
            os_hint = "linux"
    elif system == "Darwin":
        os_hint = "macos"
    elif system == "Windows":
        os_hint = "windows-native"
        detail_parts.append("(native)")

    return {
        "name": "os",
        "ok": os_hint in ("linux", "wsl2", "macos"),
        "detail": " ".join(detail_parts),
        "os_hint": os_hint,
        "hint": "WSL2 is recommended on Windows" if os_hint == "windows-native" else "",
    }


def _check_opencode() -> Dict[str, Any]:
    """Check opencode CLI availability (provider)."""
    path = shutil.which("opencode")
    ok = path is not None
    version = _run(["opencode", "--version"]) if ok else None
    return {
        "name": "opencode",
        "ok": ok,
        "detail": version or (f"found at {path}" if path else "not found"),
        "hint": "Provider CLI not available; only local readonly commands will work" if not ok else "",
    }


def _check_global_config() -> Dict[str, Any]:
    """Check global config file existence."""
    from harness.config.paths import get_global_config_path
    path = get_global_config_path()
    exists = os.path.isfile(path)
    return {
        "name": "global_config",
        "ok": exists,
        "detail": path if exists else f"{path} (not found)",
        "hint": "Run 'harness config init' to create default config" if not exists else "",
    }


def _check_runtime_dir() -> Dict[str, Any]:
    """Check that .harness/runtime/ directory exists (in current project)."""
    from harness.config.paths import get_global_config_dir
    runtime_dir = os.path.join(get_global_config_dir(), "runtime")
    exists = os.path.isdir(runtime_dir)
    return {
        "name": "runtime_dir",
        "ok": exists,
        "detail": runtime_dir if exists else f"{runtime_dir} (not found)",
        "hint": "Created automatically when running commands" if not exists else "",
    }


_CHECKS = [
    _check_python,
    _check_git,
    _check_pytest,
    _check_os,
    _check_opencode,
    _check_global_config,
    _check_runtime_dir,
]


def run_doctor(quiet: bool = False) -> List[Dict[str, Any]]:
    """Run all doctor checks and return results.

    Args:
        quiet: If True, suppress progress output to stderr.

    Returns:
        List of check result dicts.
    """
    if not quiet:
        print("🔍 Running Harness runtime doctor...", file=sys.stderr)

    results = []
    for check_fn in _CHECKS:
        result = check_fn()
        results.append(result)
        if not quiet:
            icon = "✅" if result["ok"] else "⚠️ " if result.get("hint") else "❌"
            print(f"  {icon} {result['name']}: {result['detail']}", file=sys.stderr)

    return results


def doctor_summary(results: Optional[List[Dict[str, Any]]] = None) -> str:
    """Generate a user-friendly doctor summary string."""
    if results is None:
        results = run_doctor(quiet=True)

    lines = ["# Harness Runtime Doctor"]
    all_ok = True
    for r in results:
        icon = "✅" if r["ok"] else "⚠️ "
        lines.append(f"{icon} **{r['name']}**: {r['detail']}")
        if not r["ok"] and r.get("hint"):
            lines.append(f"     {r['hint']}")
        if not r["ok"]:
            all_ok = False

    lines.append("")
    if all_ok:
        lines.append("**All checks passed.**")
    else:
        issues = sum(1 for r in results if not r["ok"])
        lines.append(f"**{issues} issue(s) found.**")
    return "\n".join(lines)
