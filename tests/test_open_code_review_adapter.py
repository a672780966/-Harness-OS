from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_ocr_config_exists():
    assert (ROOT / ".harness/config/open_code_review.yaml").exists()


def test_ocr_script_exists():
    assert (ROOT / ".harness/scripts/hermes_open_code_review.py").exists()


def test_ocr_prompt_template_exists():
    assert (ROOT / ".harness/review/open-code-review/prompts/OCR_REVIEW_PROMPT_TEMPLATE.md").exists()


def test_ocr_config_review_only():
    with (ROOT / ".harness/config/open_code_review.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["safety"]["review_only"] is True
    assert data["safety"]["forbid_code_edit"] is True
    assert data["safety"]["forbid_patch_generation"] is True
    assert data["safety"]["forbid_push"] is True
    assert data["safety"]["forbid_merge"] is True
    assert data["safety"]["forbid_deploy"] is True


def test_ocr_script_help():
    proc = subprocess.run(
        [sys.executable, ".harness/scripts/hermes_open_code_review.py", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0
    assert "Open Code Review" in proc.stdout


def test_ocr_cli_prepare_registered():
    proc = subprocess.run(
        [sys.executable, ".harness/scripts/hermes.py", "ocr-prepare", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0
    assert "--task-envelope" in proc.stdout
    assert "--result-envelope" in proc.stdout


def test_ocr_cli_run_registered():
    proc = subprocess.run(
        [sys.executable, ".harness/scripts/hermes.py", "ocr-run", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0
    assert "--task-envelope" in proc.stdout
    assert "--result-envelope" in proc.stdout


def test_tools_yaml_has_open_code_review_role():
    with (ROOT / ".harness/config/tools.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    ocr = data["tools"]["open_code_review"]
    assert ocr["role"] == "first_round_machine_review_gate"
    assert ocr["can_edit_code"] is False
    assert ocr["can_change_state"] is False
    assert ocr["can_merge"] is False
    assert ocr["can_push"] is False
    assert ocr["can_deploy"] is False


def test_agentes_md_has_ocr_policy():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Open Code Review Adapter Policy" in text
    assert "first-round machine review gate" in text
    assert "review_envelope" in text


def test_claude_md_has_ocr_awareness():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Open Code Review Adapter Awareness" in text
    assert "first-round review gate" in text
    assert "review_envelope" in text
