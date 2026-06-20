from pathlib import Path
import subprocess
import sys
import json

import yaml

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / ".harness/scripts"))


def run(cmd, check=True):
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_config_exists():
    assert (ROOT / ".harness/config/real_tool_attestation.yaml").exists()


def test_script_exists():
    assert (ROOT / ".harness/scripts/hermes_tool_attestation.py").exists()


def test_script_help():
    proc = run([sys.executable, ".harness/scripts/hermes_tool_attestation.py", "--help"])
    assert proc.returncode == 0
    assert "attest-claude" in proc.stdout
    assert "attest-codex" in proc.stdout
    assert "status" in proc.stdout


def test_env_parser_key_value():
    """Parse KEY=VALUE format."""
    from hermes_tool_attestation import load_env_file
    tmp = ROOT / ".harness/tmp/test_env_kv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("ANTHROPIC_BASE_URL=https://opencode.ai/zen/go\nANTHROPIC_MODEL=deepseek-v4-flash\n", encoding="utf-8")
    env = load_env_file(tmp)
    assert env.get("ANTHROPIC_BASE_URL") == "https://opencode.ai/zen/go"
    assert env.get("ANTHROPIC_MODEL") == "deepseek-v4-flash"
    tmp.unlink(missing_ok=True)


def test_env_parser_export():
    """Parse export KEY=VALUE format."""
    from hermes_tool_attestation import load_env_file
    tmp = ROOT / ".harness/tmp/test_env_export"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("export ANTHROPIC_BASE_URL='https://opencode.ai/zen/go'\nexport ANTHROPIC_MODEL=\"deepseek-v4-flash\"\n", encoding="utf-8")
    env = load_env_file(tmp)
    assert env.get("ANTHROPIC_BASE_URL") == "https://opencode.ai/zen/go"
    assert env.get("ANTHROPIC_MODEL") == "deepseek-v4-flash"
    tmp.unlink(missing_ok=True)


def test_no_api_key_plaintext_in_attestation():
    """attestation JSON must not contain plaintext API key."""
    run_dir = ROOT / ".harness/real-tools/runs"
    for f in run_dir.glob("*_attestation.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        provider = data.get("provider", {})
        assert "api_key" not in json.dumps(provider).lower() or provider.get("api_key_present") is not None
        raw = f.read_text(encoding="utf-8")
        assert "sk-" not in raw, f"API key found in attestation: {f}"


def test_deepseek_400_classified_as_compatibility_warning():
    """DeepSeek 400 must be provider_compatibility_warning, not routing_auth_failed."""
    from hermes_tool_attestation import classify_claude_error
    result = classify_claude_error(
        "API Error: 400 Error from provider (DeepSeek): missing field",
        "",
        exit_code=1,
    )
    assert result["provider_compatibility_warning"] is True
    assert result["routing_auth_fixed"] is True


def test_not_logged_in_classified_as_routing_auth_failed():
    """'Not logged in' must be routing_auth_failed."""
    from hermes_tool_attestation import classify_claude_error
    result = classify_claude_error(
        "Not logged in · Please run /login",
        "",
        exit_code=1,
    )
    assert result["routing_auth_fixed"] is False


def test_cli_commands_available():
    proc = run([sys.executable, ".harness/scripts/hermes.py", "--help"])
    assert "tool-attest-claude" in proc.stdout
    assert "tool-attest-codex" in proc.stdout
    assert "tool-attestation-status" in proc.stdout


def test_attestation_schema():
    """Attestation JSON must have all required fields."""
    run_dir = ROOT / ".harness/real-tools/runs"
    for f in run_dir.glob("*_attestation.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        required = [
            "version", "task_id", "trace_id", "tool", "mode",
            "binary_path", "binary_version", "provider_env_loaded",
            "provider", "process", "stdout_ref", "stderr_ref",
            "routing_auth_fixed", "provider_compatibility_warning",
            "compatibility_notes", "created_at",
        ]
        for r in required:
            assert r in data, f"Missing field '{r}' in {f}"
        proc = data.get("process", {})
        for pf in ["pid", "ppid", "cwd", "worktree", "command_line_redacted",
                     "started_at", "ended_at", "exit_code"]:
            assert pf in proc, f"Missing process field '{pf}' in {f}"
