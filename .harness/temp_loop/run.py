#!/usr/bin/env python3
"""
Temporary Loop Runner v1
Codex ↔ Hermes ↔ OpenCode 自动循环执行器

Usage:
  cd /repo && python .harness/temp_loop/run.py "objective text"

Role:
  Hermes = dispatcher + evidence collector (not planner, not reviewer, not gatekeeper)
  Codex = planner / reviewer / gatekeeper / emergency implementer
  OpenCode = implementation worker + self-reviewer
"""
import json, os, sys, subprocess, uuid, datetime, re, shutil, textwrap, time

TRACE_ID = uuid.uuid4().hex[:12]
PROJECT_ROOT = os.getcwd()
LOOP_DIR = f"{PROJECT_ROOT}/.harness/temp_loop/{TRACE_ID}"
MAX_REPAIR_ROUNDS = 3

CODEX_CMD = ["codex", "exec", "--model", "gpt-5.5", "--sandbox", "danger-full-access"]
OPENCODE_CMD = ["opencode", "run", "--model", "opencode/deepseek-v4-flash-free"]

# ---- Helpers ----

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def ts():
    return datetime.datetime.utcnow().isoformat() + "Z"

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def write_text(path, text):
    with open(path, "w") as f:
        f.write(text)

def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read()

def append_jsonl(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ---- State & Audit ----

state_log = []
audit_log = []

def state_transition(from_state, to_state, reason, evidence_ref=""):
    r = {
        "trace_id": TRACE_ID,
        "from": from_state,
        "to": to_state,
        "reason": reason,
        "evidence_ref": evidence_ref,
        "created_at": ts()
    }
    state_log.append(r)
    append_jsonl(f"{LOOP_DIR}/state_transitions.jsonl", r)
    print(f"  [STATE] {from_state} → {to_state}: {reason}")

def audit_event(event, actor, reason, evidence_ref=""):
    r = {
        "trace_id": TRACE_ID,
        "event": event,
        "actor": actor,
        "reason": reason,
        "evidence_ref": evidence_ref,
        "created_at": ts()
    }
    audit_log.append(r)
    append_jsonl(f"{LOOP_DIR}/audit_events.jsonl", r)
    print(f"  [AUDIT] [{actor}] {event}: {reason}")

# ---- Subprocess runners ----

def run_codex(prompt_text, timeout=300):
    """Call Codex CLI with prompt via stdin, return (raw_output, parsed_json)"""
    # Clean up potential stale locks
    for lock_pattern in ["/home/ctyun/.codex/.tmp/plugins.sync.lock"]:
        if os.path.exists(lock_pattern):
            try: os.remove(lock_pattern)
            except: pass
    try:
        proc = subprocess.run(
            CODEX_CMD,
            input=prompt_text.encode("utf-8"),
            capture_output=True,
            cwd=PROJECT_ROOT,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print("  [WARN] codex timed out after {timeout}s")
        return None, None
    raw = (proc.stdout or b"").decode("utf-8", errors="replace")
    # Try to extract JSON from code block or last JSON object
    parsed = extract_last_json(raw)
    if parsed is None:
        # fallback: try whole output as JSON
        cleaned = raw.strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    return raw, parsed

def run_opencode(prompt_text, timeout=300):
    """Call OpenCode CLI with prompt via stdin, return (raw_output, parsed_json)"""
    try:
        proc = subprocess.run(
            OPENCODE_CMD,
            input=prompt_text.encode("utf-8"),
            capture_output=True,
            cwd=PROJECT_ROOT,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"  [WARN] opencode timed out after {timeout}s")
        return None, None
    raw = (proc.stdout or b"").decode("utf-8", errors="replace")
    parsed = extract_last_json(raw)
    if parsed is None:
        try:
            parsed = json.loads(raw.strip())
        except json.JSONDecodeError:
            pass
    return raw, parsed

def extract_last_json(text):
    """Extract the last JSON object or array from text, handling ```json fences."""
    # Try ```json ... ``` blocks first
    blocks = re.findall(r'```(?:json)?\s*\n?(.*?)```', text, re.DOTALL)
    for block in reversed(blocks):
        stripped = block.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            continue
    # Try outermost { ... } or [ ... ]
    for opener, closer in [('{', '}'), ('[', ']')]:
        start = text.rfind(opener)
        if start >= 0:
            end = text.rfind(closer)
            if end > start:
                candidate = text[start:end+1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    return None

# ---- Diff / test helpers ----

def capture_diff():
    proc = subprocess.run(["git", "diff"], capture_output=True, cwd=PROJECT_ROOT, timeout=30)
    return proc.stdout.decode("utf-8", errors="replace")

def capture_diff_stat():
    proc = subprocess.run(["git", "diff", "--stat"], capture_output=True, cwd=PROJECT_ROOT, timeout=30)
    return proc.stdout.decode("utf-8", errors="replace").strip()

def run_pytest(path=None):
    cmd = ["python", "-m", "pytest", "-x", "-q", "--no-header"]
    if path:
        cmd.append(path)
    proc = subprocess.run(cmd, capture_output=True, cwd=PROJECT_ROOT, timeout=180)
    out = (proc.stdout or b"").decode("utf-8", errors="replace")
    err = (proc.stderr or b"").decode("utf-8", errors="replace")
    return {
        "exit_code": proc.returncode,
        "stdout": out,
        "stderr": err,
        "passed": proc.returncode == 0
    }

# ---- Phase: Codex Planning ----

BUILTIN_PLANNER_PROMPT = """You are Codex Planner in Harness OS Temporary Loop.
Your role: read the project graph, confirm task validity, produce structured JSON output.

RULES:
1. Read the codebase to understand the project graph before planning.
2. Determine if this task should be executed.
3. Output ONLY valid JSON wrapped in ```json``` code block.
4. Do NOT output any other text outside the JSON block.
5. Do NOT implement anything. Do NOT edit files.

OUTPUT FORMAT (you must follow exactly):
```json
{{
  "status": "PLANNED",
  "graph_confirmation": {{
    "known_graph_nodes": ["list", "of", "modules", "relevant"],
    "target_node": "the main module this task targets",
    "reason_to_act": "why this task makes sense in the project graph",
    "affected_subsystems": ["list"],
    "duplicate_risk": "is this duplicating existing capability?",
    "next_graph_step": "what the next step after this task should be"
  }},
  "task_envelope": {{
    "protocol": "temporary-loop/v1",
    "trace_id": "{trace_id}",
    "task_id": "task-001",
    "objective": "",
    "acceptance_criteria": [],
    "allowed_actions": ["read files", "write docs/", "run pytest", "run git status", "run git diff"],
    "blocked_actions": ["git push", "git merge", "git tag", "git reset", "git clean", "force push", "rewrite history"],
    "expected_outputs": []
  }}
}}
```

OBJECTIVE:
{objective}

PROJECT CONTEXT (current git status + diff):
{diff_stat}

Now read the repo and output your plan as JSON.
"""

def phase_codex_planning(objective):
    print("\n=== PHASE: Codex Planning ===")
    state_transition("created", "codex_planning", "Starting Codex planner")
    audit_event("Codex planning started", "hermes", "Invoking Codex Planner for objective")

    diff_stat = capture_diff_stat()
    prompt = BUILTIN_PLANNER_PROMPT.format(
        trace_id=TRACE_ID,
        objective=objective,
        diff_stat=diff_stat
    )

    write_text(f"{LOOP_DIR}/planner_prompt.md", prompt)
    audit_event("Codex planner prompt written", "hermes", "", f"{LOOP_DIR}/planner_prompt.md")

    print("  Calling Codex Planner...")
    raw, parsed = run_codex(prompt, timeout=360)

    write_text(f"{LOOP_DIR}/planner_response_raw.txt", raw or "(no output)")
    audit_event("Codex planner raw output saved", "hermes", "", f"{LOOP_DIR}/planner_response_raw.txt")

    if parsed is None:
        print("  [ERROR] Could not parse Codex planner JSON response")
        write_text(f"{LOOP_DIR}/planner_response.json", json.dumps({
            "status": "PLANNING_FAILED",
            "error": "Could not parse JSON from Codex output",
            "raw_snippet": (raw or "")[:2000]
        }, indent=2))
        state_transition("codex_planning", "blocked_requires_user_approval",
                         "Codex planner JSON parsing failed")
        return None

    write_json(f"{LOOP_DIR}/planner_response.json", parsed)
    audit_event("Codex planner response saved", "codex", f"status={parsed.get('status')}",
                f"{LOOP_DIR}/planner_response.json")

    if parsed.get("status") != "PLANNED":
        print(f"  [BLOCKED] Codex returned status={parsed.get('status')}")
        state_transition("codex_planning", "blocked_requires_user_approval",
                         f"Codex did not approve: {parsed.get('status')}")
        return None

    # Save TaskEnvelope
    te = parsed.get("task_envelope", {})
    te["trace_id"] = TRACE_ID
    write_json(f"{LOOP_DIR}/task_envelope.json", te)
    audit_event("TaskEnvelope created", "hermes", f"task_id={te.get('task_id','')}",
                f"{LOOP_DIR}/task_envelope.json")
    state_transition("codex_planning", "task_envelope_ready",
                     f"Codex approved task: {te.get('objective','')[:80]}")

    print(f"  TaskEnvelope: {te.get('objective','')[:100]}")
    return te

# ---- Phase: OpenCode Implementation ----

OPERATOR_IMPL_PROMPT = """You are OpenCode Implementation Worker in Harness OS Temporary Loop.
Your role: implement the task described in the TaskEnvelope, output structured JSON.

RULES:
1. Read the TaskEnvelope below carefully.
2. Implement according to acceptance criteria.
3. Run tests after implementation.
4. Do self-review after implementation.
5. Output ONLY valid JSON wrapped in ```json``` code block.
6. Do NOT output any other text outside the JSON block.
7. Do NOT git push, git merge, git tag, force push, or rewrite history.

OUTPUT FORMAT:
```json
{{
  "status": "IMPLEMENTED | NEEDS_REPAIR | BLOCKED",
  "changed_files": [],
  "commands_run": [],
  "test_results": [],
  "code_meaning_report": {{
    "what_changed": "",
    "why_changed": "",
    "files_touched": [],
    "behavioral_impact": "",
    "risks": "",
    "what_was_not_changed": ""
  }},
  "self_review": {{
    "issues_found": [],
    "repairs_applied": [],
    "remaining_risks": []
  }}
}}
```

TASK ENVELOPE:
{task_envelope_json}

CURRENT GIT DIFF (before starting):
{diff_before}

"""

def phase_opencode_implementation(task_envelope, repair_round=0, repair_prompt_text=None):
    tag = f"repair_round_{repair_round}" if repair_round > 0 else "initial"
    print(f"\n=== PHASE: OpenCode Implementation ({tag}) ===")

    if repair_round == 0:
        state_transition("task_envelope_ready", "dispatched_to_opencode",
                         "Dispatching to OpenCode for implementation")
    else:
        state_transition(f"repair_required", f"opencode_repair_round_{repair_round}",
                         f"OpenCode repair round {repair_round}")

    audit_event("OpenCode dispatched", "hermes", f"round={tag}",
                f"{LOOP_DIR}/task_envelope.json")

    diff_before = capture_diff()
    te_json = json.dumps(task_envelope, indent=2, ensure_ascii=False)

    if repair_prompt_text:
        prompt = repair_prompt_text
    else:
        prompt = OPERATOR_IMPL_PROMPT.format(
            task_envelope_json=te_json,
            diff_before=diff_before or "(no prior changes)"
        )

    # Write prompt
    if repair_round == 0:
        opencode_prompt_path = f"{LOOP_DIR}/opencode_prompt.md"
    else:
        opencode_prompt_path = f"{LOOP_DIR}/repair_round_{repair_round}/opencode_repair_prompt.md"
    os.makedirs(os.path.dirname(opencode_prompt_path), exist_ok=True)
    write_text(opencode_prompt_path, prompt)
    audit_event("OpenCode prompt written", "hermes", f"round={tag}", opencode_prompt_path)

    print(f"  Calling OpenCode (timeout=600s)...")
    raw, parsed = run_opencode(prompt, timeout=600)

    # Save raw output
    if repair_round == 0:
        raw_path = f"{LOOP_DIR}/opencode_response_raw.txt"
        json_path = f"{LOOP_DIR}/opencode_response.json"
    else:
        rd = f"{LOOP_DIR}/repair_round_{repair_round}"
        os.makedirs(rd, exist_ok=True)
        raw_path = f"{rd}/opencode_repair_response_raw.txt"
        json_path = f"{rd}/opencode_repair_response.json"

    write_text(raw_path, raw or "(no output)")
    audit_event("OpenCode raw output saved", "hermes", f"round={tag}", raw_path)

    if parsed is None:
        print("  [ERROR] Could not parse OpenCode JSON response")
        parsed = {
            "status": "BLOCKED",
            "error": "JSON parse failure",
            "changed_files": [],
            "commands_run": [],
            "test_results": [],
            "code_meaning_report": {
                "what_changed": "OpenCode failed to produce valid JSON",
                "why_changed": "N/A",
                "files_touched": [],
                "behavioral_impact": "N/A",
                "risks": "Unknown",
                "what_was_not_changed": "Everything"
            },
            "self_review": {
                "issues_found": ["JSON parse error from OpenCode"],
                "repairs_applied": [],
                "remaining_risks": ["Cannot verify implementation"]
            }
        }
        write_json(json_path, parsed)
        return parsed, diff_before

    write_json(json_path, parsed)
    audit_event("OpenCode result saved", "opencode", f"status={parsed.get('status')}, round={tag}",
                json_path)

    # Create ResultEnvelope
    result_env = {
        "protocol": "temporary-loop/v1",
        "trace_id": TRACE_ID,
        "task_id": task_envelope.get("task_id", "task-001"),
        "round": tag,
        "status": parsed.get("status", "UNKNOWN"),
        "worker": "opencode",
        "changed_files": parsed.get("changed_files", []),
        "diff_after": capture_diff(),
        "code_meaning": parsed.get("code_meaning_report", {}),
        "self_review": parsed.get("self_review", {}),
        "created_at": ts()
    }

    if repair_round == 0:
        result_path = f"{LOOP_DIR}/result_envelope.json"
    else:
        result_path = f"{LOOP_DIR}/repair_round_{repair_round}/result_envelope.json"
    write_json(result_path, result_env)

    if parsed.get("status") == "IMPLEMENTED":
        state_transition(f"dispatched_to_opencode" if repair_round == 0 else f"opencode_repair_round_{repair_round}",
                         "result_envelope_ready", "OpenCode implementation complete")
    else:
        state_transition(f"dispatched_to_opencode" if repair_round == 0 else f"opencode_repair_round_{repair_round}",
                         "result_envelope_ready", f"OpenCode status: {parsed.get('status')}")

    audit_event("ResultEnvelope created", "hermes", f"status={parsed.get('status')}", result_path)
    return parsed, diff_before

# ---- Phase: Codex Review ----

CODEX_REVIEW_PROMPT = """You are Codex Reviewer in Harness OS Temporary Loop.
Your role: review the implementation results against acceptance criteria, produce structured JSON.

RULES:
1. Read the TaskEnvelope and ResultEnvelope carefully.
2. Check if acceptance criteria are met.
3. Check if self-review is adequate.
4. Check if tests pass.
5. Output ONLY valid JSON wrapped in ```json``` code block.
6. Do NOT edit files. Do NOT implement anything.

OUTPUT FORMAT:
```json
{{
  "status": "DONE | REPAIR | BLOCKED_REQUIRES_USER_APPROVAL",
  "summary": "",
  "graph_verdict": {{
    "matches_graph": true,
    "can_enter_next_step": false,
    "reason": ""
  }},
  "review": {{
    "passed": false,
    "blocking_issues": [],
    "required_repairs": [],
    "evidence_checked": []
  }},
  "final_evidence_required": []
}}
```

TASK ENVELOPE:
{task_envelope_json}

RESULT ENVELOPE:
{result_envelope_json}

CURRENT DIFF:
{current_diff}

TEST RESULTS:
{test_results}

PREVIOUS REVIEWS (if any):
{previous_reviews}
"""

def phase_codex_review(task_envelope, result_envelope, repair_round=0, previous_reviews=None):
    tag = f"round_{repair_round}" if repair_round > 0 else "initial"
    if repair_round == 0:
        print("\n=== PHASE: Codex Review ===")
        state_transition("result_envelope_ready", "codex_reviewing", "Sending to Codex for review")
    elif repair_round > 0 and repair_round <= MAX_REPAIR_ROUNDS:
        print(f"\n=== PHASE: Codex Review ({tag}) ===")
        state_transition(f"opencode_repair_round_{repair_round}",
                         f"codex_reviewing_round_{repair_round}",
                         f"Codex reviewing repair round {repair_round}")

    audit_event("Codex review started", "hermes", f"round={tag}",
                f"{LOOP_DIR}/result_envelope.json")

    te_json = json.dumps(task_envelope, indent=2, ensure_ascii=False)
    re_json = json.dumps(result_envelope, indent=2, ensure_ascii=False)
    current_diff = capture_diff()
    test_res = run_pytest()
    test_text = json.dumps(test_res, indent=2, ensure_ascii=False)
    prev_text = json.dumps(previous_reviews or [], indent=2, ensure_ascii=False)

    prompt = CODEX_REVIEW_PROMPT.format(
        task_envelope_json=te_json,
        result_envelope_json=re_json,
        current_diff=current_diff or "(none)",
        test_results=test_text,
        previous_reviews=prev_text
    )

    if repair_round == 0:
        prompt_path = f"{LOOP_DIR}/review_prompt.md"
    else:
        prompt_path = f"{LOOP_DIR}/repair_round_{repair_round}/codex_review_prompt.md"
    os.makedirs(os.path.dirname(prompt_path), exist_ok=True)
    write_text(prompt_path, prompt)
    audit_event("Codex review prompt written", "hermes", f"round={tag}", prompt_path)

    print("  Calling Codex Reviewer...")
    raw, parsed = run_codex(prompt, timeout=360)

    if repair_round == 0:
        raw_review_path = f"{LOOP_DIR}/review_response_raw.txt"
        json_review_path = f"{LOOP_DIR}/review_response.json"
    else:
        rd = f"{LOOP_DIR}/repair_round_{repair_round}"
        os.makedirs(rd, exist_ok=True)
        raw_review_path = f"{rd}/codex_review_response_raw.txt"
        json_review_path = f"{rd}/codex_review_response.json"

    write_text(raw_review_path, raw or "(no output)")
    audit_event("Codex review raw output saved", "hermes", f"round={tag}", raw_review_path)

    if parsed is None:
        print("  [ERROR] Could not parse Codex review JSON")
        parsed = {
            "status": "BLOCKED_REQUIRES_USER_APPROVAL",
            "summary": "Codex review JSON parsing failed",
            "graph_verdict": {"matches_graph": False, "can_enter_next_step": False,
                              "reason": "Codex output not parseable"},
            "review": {"passed": False, "blocking_issues": ["Codex JSON parse failure"],
                       "required_repairs": ["Manual inspection required"],
                       "evidence_checked": []},
            "final_evidence_required": []
        }
        write_json(json_review_path, parsed)
        audit_event("Codex review response saved (fallback)", "hermes",
                    f"status=BLOCKED_REQUIRES_USER_APPROVAL (parse failed)", json_review_path)
        return parsed

    write_json(json_review_path, parsed)
    audit_event("Codex review response saved", "codex", f"status={parsed.get('status')}",
                json_review_path)

    s = parsed.get("status", "")
    if s == "DONE":
        state_transition(f"codex_reviewing" if repair_round == 0 else f"codex_reviewing_round_{repair_round}",
                         "final_ready", "Codex review passed")
    elif s == "REPAIR":
        state_transition(f"codex_reviewing" if repair_round == 0 else f"codex_reviewing_round_{repair_round}",
                         "repair_required", f"Codex requested repairs: {parsed.get('summary','')[:80]}")
    else:
        state_transition(f"codex_reviewing" if repair_round == 0 else f"codex_reviewing_round_{repair_round}",
                         "blocked_requires_user_approval",
                         f"Codex blocked: {parsed.get('summary','')[:80]}")

    print(f"  Review verdict: {s}")
    return parsed

# ---- Phase: Emergency Implementation ----

EMERGENCY_PROMPT = """You are Codex Emergency Implementer in Harness OS Temporary Loop.
OpenCode failed to meet acceptance criteria after {repair_rounds} repair rounds.
You must now implement the required fixes directly.

RULES:
1. Read all context below carefully.
2. Implement the required repairs.
3. Run tests after implementation.
4. Output ONLY valid JSON wrapped in ```json``` code block.
5. Do NOT git push, git merge, git tag, force push, or rewrite history.

OUTPUT FORMAT:
```json
{{
  "status": "IMPLEMENTED | BLOCKED_REQUIRES_USER_APPROVAL",
  "summary": "",
  "changed_files": [],
  "commands_run": [],
  "repairs_applied": [],
  "remaining_risks": [],
  "requires_user_approval": false
}}
```

CONTEXT:
- TaskEnvelope: {task_envelope_json}
- OpenCode results: {opencode_results_json}
- Codex reviews: {codex_reviews_json}
- Latest diff: {current_diff}
- Test results: {test_results}

Required repairs from Codex:
{required_repairs}
"""

FINAL_GATE_PROMPT = """You are Codex Final Gate in Harness OS Temporary Loop.
Review the emergency implementation and determine if it is complete.

RULES:
1. Read the emergency implementation results.
2. Check if all required repairs were applied.
3. Check if tests pass.
4. Output ONLY valid JSON wrapped in ```json``` code block.

OUTPUT FORMAT:
```json
{{
  "status": "DONE | BLOCKED_REQUIRES_USER_APPROVAL",
  "summary": "",
  "review": {{
    "passed": false,
    "blocking_issues": [],
    "evidence_checked": []
  }},
  "final_evidence_required": []
}}
```

CONTEXT:
- TaskEnvelope: {task_envelope_json}
- Emergency Implementation: {emergency_json}
- Diff after emergency: {current_diff}
- Test results: {test_results}
"""

def phase_emergency(task_envelope, opencode_results, codex_reviews):
    print("\n=== PHASE: Codex Emergency Implementation ===")
    state_transition("repair_required", "codex_emergency_implementation",
                     "OpenCode failed 3 rounds, Codex takes over")
    audit_event("Codex emergency implementation started", "hermes",
                "OpenCode failed all repair rounds", "")

    te_json = json.dumps(task_envelope, indent=2, ensure_ascii=False)
    oc_json = json.dumps(opencode_results, indent=2, ensure_ascii=False)
    cr_json = json.dumps(codex_reviews, indent=2, ensure_ascii=False)
    current_diff = capture_diff()
    test_res = run_pytest()
    test_text = json.dumps(test_res, indent=2, ensure_ascii=False)

    # Collect required repairs from last review
    required_repairs = []
    if codex_reviews:
        last_review = codex_reviews[-1]
        required_repairs = last_review.get("review", {}).get("required_repairs", [])
    repair_text = json.dumps(required_repairs, indent=2, ensure_ascii=False)

    prompt = EMERGENCY_PROMPT.format(
        repair_rounds=MAX_REPAIR_ROUNDS,
        task_envelope_json=te_json,
        opencode_results_json=oc_json,
        codex_reviews_json=cr_json,
        current_diff=current_diff or "(none)",
        test_results=test_text,
        required_repairs=repair_text
    )

    emergency_dir = f"{LOOP_DIR}/codex_emergency"
    os.makedirs(emergency_dir, exist_ok=True)
    write_text(f"{emergency_dir}/codex_emergency_repair_prompt.md", prompt)
    audit_event("Codex emergency prompt written", "hermes", "",
                f"{emergency_dir}/codex_emergency_repair_prompt.md")

    print("  Calling Codex Emergency Implementer (timeout=600s)...")
    raw, parsed = run_codex(prompt, timeout=600)

    write_text(f"{emergency_dir}/codex_emergency_raw.txt", raw or "(no output)")
    audit_event("Codex emergency raw output saved", "hermes", "", f"{emergency_dir}/codex_emergency_raw.txt")

    if parsed is None:
        print("  [ERROR] Codex emergency JSON parse failed")
        parsed = {"status": "BLOCKED_REQUIRES_USER_APPROVAL", "summary": "JSON parse failure",
                  "changed_files": [], "commands_run": [], "repairs_applied": [],
                  "remaining_risks": ["Codex emergency output not parseable"],
                  "requires_user_approval": True}
        write_json(f"{emergency_dir}/codex_emergency_repair_response.json", parsed)
        return None

    write_json(f"{emergency_dir}/codex_emergency_repair_response.json", parsed)
    audit_event("Codex emergency response saved", "codex", f"status={parsed.get('status')}",
                f"{emergency_dir}/codex_emergency_repair_response.json")

    # ---- Final Gate ----
    print("\n=== PHASE: Codex Final Gate ===")
    state_transition("codex_emergency_implementation", "codex_final_gate",
                     "Codex emergency done, running final gate")
    audit_event("Codex final gate started", "hermes", "", "")

    current_diff = capture_diff()
    test_res = run_pytest()
    test_text = json.dumps(test_res, indent=2, ensure_ascii=False)
    em_json = json.dumps(parsed, indent=2, ensure_ascii=False)

    fg_prompt = FINAL_GATE_PROMPT.format(
        task_envelope_json=te_json,
        emergency_json=em_json,
        current_diff=current_diff or "(none)",
        test_results=test_text
    )

    write_text(f"{emergency_dir}/codex_final_gate_prompt.md", fg_prompt)
    audit_event("Codex final gate prompt written", "hermes", "",
                f"{emergency_dir}/codex_final_gate_prompt.md")

    print("  Calling Codex Final Gate...")
    raw2, parsed2 = run_codex(fg_prompt, timeout=360)

    write_text(f"{emergency_dir}/codex_final_gate_raw.txt", raw2 or "(no output)")
    if parsed2 is None:
        parsed2 = {"status": "BLOCKED_REQUIRES_USER_APPROVAL", "summary": "Final gate JSON parse failure",
                   "review": {"passed": False, "blocking_issues": ["JSON parse failure"],
                              "evidence_checked": []},
                   "final_evidence_required": []}

    write_json(f"{emergency_dir}/codex_final_gate_response.json", parsed2)
    audit_event("Codex final gate response saved", "codex", f"status={parsed2.get('status')}",
                f"{emergency_dir}/codex_final_gate_response.json")

    state_transition("codex_final_gate", "final_evidence_ready" if parsed2.get("status") == "DONE" else "blocked_requires_user_approval",
                     f"Codex final gate: {parsed2.get('status')}")
    return parsed2

# ---- Final Evidence ----

FINAL_EVIDENCE_SCHEMA = {
    "trace_id": "",
    "protocol": "temporary-loop/v1",
    "objective": "",
    "planner_response": "",
    "task_envelope": "",
    "opencode_results": "",
    "codex_reviews": "",
    "final_verdict": "",
    "state_transitions": "",
    "audit_events": "",
    "test_results": "",
    "diff_final": "",
    "emergency_used": False,
    "emergency_results": "",
    "created_at": ""
}

def generate_final_evidence(objective, task_envelope, planner_response, opencode_results_list,
                             codex_reviews_list, final_verdict, emergency_results=None):
    print("\n=== PHASE: Final Evidence ===")
    state_transition("final_ready", "final_evidence_ready", "Generating FinalEvidence")
    audit_event("FinalEvidence creation started", "hermes", "")

    test_res = run_pytest()
    diff_final = capture_diff()

    evidence = {
        "trace_id": TRACE_ID,
        "protocol": "temporary-loop/v1",
        "objective": objective,
        "planner_response": f"{LOOP_DIR}/planner_response.json",
        "task_envelope": f"{LOOP_DIR}/task_envelope.json",
        "opencode_results": [f"{LOOP_DIR}/opencode_response.json"] + [
            f"{LOOP_DIR}/repair_round_{i}/opencode_repair_response.json"
            for i in range(1, len(opencode_results_list))
        ] if len(opencode_results_list) > 0 else [],
        "codex_reviews": [f"{LOOP_DIR}/review_response.json"] + [
            f"{LOOP_DIR}/repair_round_{i}/codex_review_response.json"
            for i in range(1, len(codex_reviews_list))
        ] if len(codex_reviews_list) > 0 else [],
        "final_verdict": final_verdict,
        "test_results_passed": test_res.get("passed", False),
        "test_exit_code": test_res.get("exit_code"),
        "test_stdout_snippet": test_res.get("stdout", "")[:500],
        "diff_stat": capture_diff_stat(),
        "diff_full": diff_final,
        "emergency_used": emergency_results is not None,
        "emergency_results": f"{LOOP_DIR}/codex_emergency/codex_final_gate_response.json" if emergency_results else None,
        "state_transitions_path": f"{LOOP_DIR}/state_transitions.jsonl",
        "audit_events_path": f"{LOOP_DIR}/audit_events.jsonl",
        "created_at": ts()
    }

    write_json(f"{LOOP_DIR}/final_evidence.json", evidence)
    audit_event("FinalEvidence created", "hermes", f"verdict={final_verdict}",
                f"{LOOP_DIR}/final_evidence.json")
    print(f"  FinalEvidence: {LOOP_DIR}/final_evidence.json")
    return evidence

# ---- Run Report ----

def generate_run_report(objective, task_envelope, planner_response, opencode_results_list,
                         codex_reviews_list, final_verdict, emergency_results, evidence,
                         num_repair_rounds):
    print("\n=== PHASE: Run Report ===")

    report = f"""# Temporary Loop First Run Report

## Objective
{objective}

## Graph confirmation from Codex
```json
{json.dumps(planner_response.get("graph_confirmation", {}), indent=2, ensure_ascii=False) if planner_response else "N/A"}
```

## TaskEnvelope path
`{LOOP_DIR}/task_envelope.json`

## OpenCode implementation summary
{"OpenCode completed initial implementation" if opencode_results_list else "No OpenCode result"}
- Status: {opencode_results_list[0].get("status") if opencode_results_list else "N/A"}
- Changed files: {json.dumps(opencode_results_list[0].get("changed_files", []), ensure_ascii=False) if opencode_results_list else "N/A"}

## Code / document meaning report
```json
{json.dumps(opencode_results_list[0].get("code_meaning_report", {}), indent=2, ensure_ascii=False) if opencode_results_list else "N/A"}
```

## OpenCode self-review
```json
{json.dumps(opencode_results_list[0].get("self_review", {}), indent=2, ensure_ascii=False) if opencode_results_list else "N/A"}
```

## Codex review result
```json
{json.dumps(codex_reviews_list[0], indent=2, ensure_ascii=False) if codex_reviews_list else "N/A"}
```

## Repair rounds
{num_repair_rounds} repair round(s) executed.
"""
    for i in range(1, num_repair_rounds + 1):
        oc = opencode_results_list[i] if i < len(opencode_results_list) else None
        cr = codex_reviews_list[i] if i < len(codex_reviews_list) else None
        report += f"""
### Repair round {i}
- OpenCode status: {oc.get("status") if oc else "N/A"}
- Self-review issues: {json.dumps(oc.get("self_review", {}).get("issues_found", []), ensure_ascii=False) if oc else "N/A"}
- Codex review status: {cr.get("status") if cr else "N/A"}
- Required repairs: {json.dumps(cr.get("review", {}).get("required_repairs", []), ensure_ascii=False) if cr else "N/A"}
"""

    if emergency_results:
        report += f"""
## Codex emergency implementation
- Used: YES
- Emergency result: {json.dumps(emergency_results, indent=2, ensure_ascii=False)}
"""
    else:
        report += """
## Codex emergency implementation
- Used: NO (OpenCode passed all checks)
"""

    report += f"""
## FinalEvidence path
`{LOOP_DIR}/final_evidence.json`

## State transitions path
`{LOOP_DIR}/state_transitions.jsonl`
Total: {len(state_log)} transitions

## Audit events path
`{LOOP_DIR}/audit_events.jsonl`
Total: {len(audit_log)} events

## Did Hermes act only as dispatcher?
YES. Hermes did not implement code, did not review, did not plan. Only dispatched agents and collected artifacts.

## Verdict
{final_verdict}
"""

    write_text(f"{LOOP_DIR}/run_report.md", report)
    audit_event("Run report generated", "hermes", f"verdict={final_verdict}",
                f"{LOOP_DIR}/run_report.md")

    # Also write the project-level report
    docs_report = f"{PROJECT_ROOT}/docs/temp_loop_first_run_report.md"
    write_text(docs_report, report)
    audit_event("Project-level report written", "hermes", "", docs_report)
    print(f"  Report: {docs_report}")
    return report

# ---- Main ----

def main():
    objective = sys.argv[1] if len(sys.argv) > 1 else (
        "Use the temporary Codex-Hermes-OpenCode loop to audit the current "
        "Harness OS loop/governance components and produce a first machine-routed "
        "governance recovery report."
    )

    print(f"{'='*60}", flush=True)
    print(f"Temporary Loop Runner v1", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Trace ID: {TRACE_ID}", flush=True)
    print(f"Objective: {objective[:120]}", flush=True)
    print(f"Loop dir: {LOOP_DIR}", flush=True)
    print(flush=True)

    ensure_dir(LOOP_DIR)

    audit_event("Temporary loop started", "hermes", f"trace_id={TRACE_ID}", "")
    state_transition("created", "codex_planning", "Loop started")

    # Phase 1: Codex Planning
    task_envelope = phase_codex_planning(objective)
    if task_envelope is None:
        final_verdict = "BLOCKED_REQUIRES_USER_APPROVAL"
        generate_final_evidence(objective, None, None, [], [], final_verdict)
        generate_run_report(objective, None, None, [], [], final_verdict, None, None, 0)
        print(f"\n{'='*60}")
        print(f"FINAL: {final_verdict}")
        print(f"{'='*60}")
        return

    planner_response = read_json(f"{LOOP_DIR}/planner_response.json") or {}

    # Phase 2: OpenCode Implementation
    opencode_results_list = []
    codex_reviews_list = []
    num_repair_rounds = 0
    emergency_results = None
    final_verdict = "REPAIR"

    oc_result, _ = phase_opencode_implementation(task_envelope, repair_round=0)
    opencode_results_list.append(oc_result)

    # Phase 3: Codex Review (initial)
    re_json = read_json(f"{LOOP_DIR}/result_envelope.json") or {}
    review = phase_codex_review(task_envelope, re_json, repair_round=0)
    codex_reviews_list.append(review)

    # Phase 4: Repair Loop
    while review.get("status") == "REPAIR" and num_repair_rounds < MAX_REPAIR_ROUNDS:
        num_repair_rounds += 1
        print(f"\n{'='*40}")
        print(f"REPAIR ROUND {num_repair_rounds}")
        print(f"{'='*40}")

        # Build repair prompt from review
        required_repairs = review.get("review", {}).get("required_repairs", [])
        repair_prompt = f"""You are OpenCode Repair Worker in Harness OS Temporary Loop.
Your task is to fix the issues identified by Codex Reviewer.

RULES:
1. Read the issues below and fix them.
2. Run tests after fixing.
3. Output ONLY valid JSON wrapped in ```json``` code block.

ISSUES TO FIX:
{json.dumps(required_repairs, indent=2, ensure_ascii=False)}

CODEX REVIEW SUMMARY:
{review.get("summary", "")}

TASK ENVELOPE (original):
{json.dumps(task_envelope, indent=2, ensure_ascii=False)}

OUTPUT FORMAT:
```json
{{
  "status": "IMPLEMENTED | NEEDS_REPAIR | BLOCKED",
  "changed_files": [],
  "commands_run": [],
  "test_results": [],
  "code_meaning_report": {{
    "what_changed": "",
    "why_changed": "",
    "files_touched": [],
    "behavioral_impact": "",
    "risks": "",
    "what_was_not_changed": ""
  }},
  "self_review": {{
    "issues_found": [],
    "repairs_applied": [],
    "remaining_risks": []
  }}
}}
```"""

        oc_repair, _ = phase_opencode_implementation(
            task_envelope, repair_round=num_repair_rounds,
            repair_prompt_text=repair_prompt
        )
        opencode_results_list.append(oc_repair)

        # Codex re-review
        re_repair_path = f"{LOOP_DIR}/repair_round_{num_repair_rounds}/result_envelope.json"
        re_repair = read_json(re_repair_path) or {}
        review = phase_codex_review(task_envelope, re_repair,
                                     repair_round=num_repair_rounds,
                                     previous_reviews=codex_reviews_list)
        codex_reviews_list.append(review)

    # Phase 5: Emergency or Final
    if review.get("status") == "REPAIR":
        print("\n=== OpenCode failed all repair rounds ===")
        emergency_results = phase_emergency(task_envelope, opencode_results_list, codex_reviews_list)
        if emergency_results:
            fg_status = emergency_results.get("status", "BLOCKED_REQUIRES_USER_APPROVAL")
            if fg_status == "DONE":
                final_verdict = "DONE"
            else:
                final_verdict = fg_status
        else:
            final_verdict = "BLOCKED_REQUIRES_USER_APPROVAL"
    elif review.get("status") == "DONE":
        final_verdict = "DONE"
    elif review.get("status") == "BLOCKED_REQUIRES_USER_APPROVAL":
        final_verdict = "BLOCKED_REQUIRES_USER_APPROVAL"

    # Phase 6: FinalEvidence
    evidence = generate_final_evidence(
        objective, task_envelope,
        planner_response if planner_response else {},
        opencode_results_list, codex_reviews_list,
        final_verdict, emergency_results
    )

    # Phase 7: Run Report
    generate_run_report(
        objective, task_envelope,
        planner_response if planner_response else {},
        opencode_results_list, codex_reviews_list,
        final_verdict, emergency_results, evidence,
        num_repair_rounds
    )

    print(f"\n{'='*60}")
    print(f"LOOP COMPLETE")
    print(f"{'='*60}")
    print(f"Trace ID: {TRACE_ID}")
    print(f"Final Verdict: {final_verdict}")
    print(f"Repair rounds: {num_repair_rounds}")
    print(f"Emergency used: {emergency_results is not None}")
    print(f"Artifact dir: {LOOP_DIR}")
    print(f"Report: docs/temp_loop_first_run_report.md")
    print(f"Commit blocked: YES (waiting for User approval)")
    print()

    # Print summary for Hermes to report back
    summary = {
        "trace_id": TRACE_ID,
        "loop_dir": LOOP_DIR,
        "verdict": final_verdict,
        "num_repair_rounds": num_repair_rounds,
        "emergency_used": emergency_results is not None,
        "artifacts": {
            "planner_response": f"{LOOP_DIR}/planner_response.json",
            "task_envelope": f"{LOOP_DIR}/task_envelope.json",
            "opencode_response": f"{LOOP_DIR}/opencode_response.json",
            "result_envelope": f"{LOOP_DIR}/result_envelope.json",
            "review_response": f"{LOOP_DIR}/review_response.json",
            "final_evidence": f"{LOOP_DIR}/final_evidence.json",
            "run_report": f"{PROJECT_ROOT}/docs/temp_loop_first_run_report.md",
            "state_transitions": f"{LOOP_DIR}/state_transitions.jsonl",
            "audit_events": f"{LOOP_DIR}/audit_events.jsonl"
        },
        "commit_requires_user_approval": True
    }

    write_text(f"{LOOP_DIR}/_summary.json", json.dumps(summary, indent=2, ensure_ascii=False))
    audit_event("Temporary loop completed", "hermes",
                f"verdict={final_verdict}, waiting for user commit approval", "")

    # Print the summary JSON for the caller to parse
    print("---LOOP_SUMMARY_START---")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("---LOOP_SUMMARY_END---")


def read_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


if __name__ == "__main__":
    main()
