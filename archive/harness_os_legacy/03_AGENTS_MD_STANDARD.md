# AGENTS.md Standard for Harness OS Projects

## 1. 文件定位

`AGENTS.md` 是 Codex / Agent 进入项目后的项目入口协议。

它不是普通 README，也不是开发文档，而是：

```text id="o26dz4"
Agent 执行项目任务时必须优先读取和遵守的项目级操作规范。
```

每个被 Harness OS 管理的项目仓库根目录必须包含：

```text id="sxztxg"
AGENTS.md
```

推荐路径：

```text id="gvxhek"
repo/
  AGENTS.md
  .project/
  src/
  tests/
  docs/
```

---

## 2. 优先级规则

Codex 在执行任务时应按照以下优先级解释上下文：

```text id="ks1wjp"
1. 用户当前明确指令
2. AGENTS.md
3. .project/state/current.md
4. .project/tasks/current-task.md
5. .project/decisions/*.md
6. README.md / docs/*
7. 代码和测试本身
```

如果 `AGENTS.md` 与普通文档冲突，以 `AGENTS.md` 为准。

如果 `AGENTS.md` 与用户当前明确指令冲突，应停止并请求确认。

---

## 3. AGENTS.md 必须包含的章节

标准 `AGENTS.md` 必须包含以下章节：

```text id="h1xaza"
1. Project Identity
2. Project Goals
3. Architecture Rules
4. Repository Structure
5. Development Commands
6. Testing and Verification
7. Coding Standards
8. Context Rules
9. State and Memory Rules
10. Skill / Tool Rules
11. Permission and Approval Rules
12. Git and Delivery Rules
13. Security Rules
14. Task Completion Rules
```

---

# AGENTS.md Template

```markdown id="5d0c7m"
# AGENTS.md

## 1. Project Identity

Project Name: <PROJECT_NAME>

Project Type: <web app / backend service / CLI / library / agent harness / other>

Primary Language: <TypeScript / Python / Go / Rust / other>

Runtime: <Node.js / Python / browser / server / edge / other>

Package Manager: <pnpm / npm / yarn / uv / pip / poetry / other>

Repository Role:

This repository is managed by Harness OS and executed by a single Codex agent.

Codex is the only execution agent.

Harness OS provides workspace, context, state, skills, governance, verification, observability, and delivery.

---

## 2. Project Goals

This project exists to:

- <goal 1>
- <goal 2>
- <goal 3>

The agent must optimize for:

- correctness
- maintainability
- testability
- recoverability
- clear delivery

The agent must not optimize for:

- unnecessary abstraction
- hidden complexity
- multi-agent orchestration
- unapproved architectural changes
- unverified code changes

---

## 3. Architecture Rules

The project architecture is governed by the following rules:

1. Keep the system single-agent-first.
2. Do not introduce multi-agent orchestration unless explicitly approved.
3. Do not introduce model routing unless explicitly approved.
4. Prefer deterministic workflow for deterministic tasks.
5. Use Codex for reasoning, coding, summarization, review, and task execution.
6. Use Harness Skills for filesystem, shell, git, GitHub, browser, repo scanning, testing, and delivery.
7. Keep project state inside the repository or Harness-managed local state.
8. Do not create a separate memory repository unless explicitly approved.
9. Treat Git as the source of long-term project truth.
10. Treat `.project/` as the project operating state area.

---

## 4. Repository Structure

Expected repository structure:

```text
repo/
  AGENTS.md
  README.md
  .project/
    state/
    tasks/
    decisions/
    reports/
    checkpoints/
    sessions/
    context/
  src/
  tests/
  docs/
```

Directory meanings:

```text id="1b9e7w"
AGENTS.md
  Agent operating protocol.

.project/state/
  Current project state and durable project facts.

.project/tasks/
  Task records, active tasks, completed task summaries.

.project/decisions/
  Architecture and product decisions.

.project/reports/
  Run reports, verification reports, delivery reports.

.project/checkpoints/
  Recovery checkpoints.

.project/sessions/
  Resumable session metadata.

.project/context/
  Context packs and context summaries.

src/
  Product source code.

tests/
  Test code.

docs/
  Human-facing documentation.
```

If the actual repository structure differs, Codex must inspect the repository before making changes.

---

## 5. Development Commands

Codex must use the project’s declared commands.

Install dependencies:

```bash id="wzfd0p"
<INSTALL_COMMAND>
```

Run development server:

```bash id="b45nfy"
<DEV_COMMAND>
```

Build:

```bash id="owohde"
<BUILD_COMMAND>
```

Run tests:

```bash id="lfw83c"
<TEST_COMMAND>
```

Run lint:

```bash id="ycdjgj"
<LINT_COMMAND>
```

Run typecheck:

```bash id="mny28u"
<TYPECHECK_COMMAND>
```

If a command is missing, Codex must infer from package files only after inspecting:

```text id="43avux"
package.json
pnpm-lock.yaml
yarn.lock
package-lock.json
pyproject.toml
requirements.txt
go.mod
Cargo.toml
Makefile
```

Codex must not invent commands without checking the repository.

---

## 6. Testing and Verification

Every meaningful code change must be verified.

Required verification order:

```text id="tdldiu"
1. static inspection
2. lint if available
3. typecheck if available
4. unit tests if available
5. integration tests if relevant
6. build if relevant
7. manual risk review
```

Codex must record verification results in:

```text id="tmy2sx"
.project/reports/
```

If tests cannot be run, Codex must record:

```text id="odwq5b"
- which command was attempted
- why it failed or was skipped
- what risk remains
```

A task is not complete until verification status is explicitly reported.

---

## 7. Coding Standards

General rules:

1. Prefer small, focused changes.
2. Preserve existing architecture unless instructed otherwise.
3. Match the existing code style.
4. Avoid unnecessary dependencies.
5. Avoid broad rewrites.
6. Avoid unrelated formatting changes.
7. Do not remove tests unless explicitly approved.
8. Do not suppress errors without explaining why.
9. Do not hardcode secrets.
10. Do not introduce hidden global state unless approved.

For TypeScript projects:

```text id="55jgft"
- prefer explicit types at module boundaries
- avoid `any` unless justified
- preserve strict mode compatibility
- keep public APIs stable unless instructed
```

For Python projects:

```text id="6d09dm"
- preserve typing where present
- avoid broad dynamic behavior
- prefer small functions
- keep CLI and library boundaries clear
```

---

## 8. Context Rules

Codex must build context before editing.

Required context sources:

```text id="n932h9"
1. AGENTS.md
2. current user task
3. relevant project state under .project/state/
4. relevant active task under .project/tasks/
5. relevant decisions under .project/decisions/
6. repository structure
7. relevant source files
8. relevant tests
9. current git status and diff
```

Codex must not load the entire repository blindly.

Context selection should prioritize:

```text id="qrgck5"
1. files explicitly mentioned by the user
2. files changed in current branch
3. files related by import/export or symbol reference
4. tests related to changed files
5. recent task summaries
6. architecture decisions
```

Codex must preserve a summary of important context in:

```text id="btmbkx"
.project/context/
```

---

## 9. State and Memory Rules

Project memory is part of the project workspace.

It lives under:

```text id="dmyyfq"
.project/
```

Allowed long-term project state:

```text id="2veis0"
.project/state/
.project/tasks/
.project/decisions/
.project/reports/
.project/checkpoints/
.project/context/
```

Do not create:

```text id="wvfd5i"
external memory repo
global project-specific memory repo
unapproved vector database
unapproved knowledge graph
```

Codex may write task summaries to:

```text id="8w1suy"
.project/tasks/
```

Codex may write run reports to:

```text id="lkqpdr"
.project/reports/
```

Codex may propose architecture decisions under:

```text id="cs6xes"
.project/decisions/
```

But major decision files require approval before becoming authoritative.

---

## 10. Skill / Tool Rules

Harness OS provides skills.

Skills are tools, not agents.

Allowed skill categories:

```text id="zsz9no"
filesystem
shell
git
github
browser
repo-scanner
test-runner
database
delivery
```

Codex may use skills to:

```text id="54s9oa"
read files
write files
inspect diffs
run tests
run builds
scan repository structure
create reports
prepare commits
prepare PRs
```

Codex must not use skills to:

```text id="1dkoz2"
delete large portions of the project without approval
push to main without approval
deploy without approval
expose secrets
modify governance rules without approval
modify AGENTS.md without approval
```

---

## 11. Permission and Approval Rules

The following actions require explicit approval:

```text id="10l6ts"
1. modifying AGENTS.md
2. modifying architecture rules
3. deleting files
4. deleting tests
5. changing package manager
6. adding major dependencies
7. changing public APIs
8. database migration
9. deployment
10. pushing to main
11. force push
12. rewriting git history
13. changing security policy
14. introducing multi-agent behavior
15. introducing model routing
16. adding external memory/vector infrastructure
```

The following actions may be done without approval if required by the task:

```text id="ef3mzp"
1. reading files
2. searching files
3. creating task reports
4. editing source files within task scope
5. adding or updating tests within task scope
6. running lint
7. running tests
8. running build
9. creating local checkpoints
```

If unsure, Codex must pause and request approval.

---

## 12. Git and Delivery Rules

Codex must inspect git state before changes:

```bash id="ki755s"
git status
```

Codex must avoid overwriting user changes.

Before finishing a task, Codex must provide:

```text id="9uh6vg"
- changed files
- summary of changes
- tests run
- remaining risks
- suggested commit message
```

Commit message format:

```text id="mqqcmd"
<type>(<scope>): <summary>
```

Allowed types:

```text id="iedw1x"
feat
fix
refactor
test
docs
chore
build
ci
perf
revert
```

Codex must not commit automatically unless the user or Harness policy allows it.

Codex must not push automatically unless explicitly approved.

---

## 13. Security Rules

Codex must protect secrets.

Never expose or write:

```text id="su5spy"
API keys
tokens
passwords
private keys
.env values
credentials
personal data
```

Codex must not print secret values into logs or reports.

If a secret is detected, Codex must redact it:

```text id="n4tfhb"
[REDACTED]
```

Codex must not install or execute unknown scripts without checking their source and purpose.

Codex must treat shell commands as potentially dangerous.

High-risk commands require approval:

```bash id="2214kv"
rm -rf
sudo
chmod -R
chown -R
git reset --hard
git clean -fd
git push --force
curl | sh
wget | sh
```

---

## 14. Task Completion Rules

A task is complete only when Codex has produced:

```text id="6wvclv"
1. implementation summary
2. changed files list
3. verification results
4. risk notes
5. follow-up items if any
6. project state update if needed
```

Codex must write a task summary to:

```text id="swmqj2"
.project/tasks/
```

Recommended task summary format:

```markdown id="6610g0"
# Task: <TASK_TITLE>

## Goal

## Changes Made

## Files Changed

## Verification

## Risks

## Follow-up

## Status
```

Codex must write a run report to:

```text id="0vl80j"
.project/reports/
```

Recommended run report format:

```markdown id="c54c7h"
# Run Report: <RUN_ID>

## Task

## Context Used

## Tool Calls

## Changes

## Verification

## Approval Events

## Final Status
```

---

## 15. Recovery Rules

Codex must create or request checkpoints before high-risk operations.

Checkpoint should include:

```text id="ikxmto"
git status
current branch
changed files
task id
context summary
last successful verification
```

If a task fails, Codex must record:

```text id="3n9q2p"
what failed
where it failed
commands run
error output summary
recommended recovery path
```

Failure reports go to:

```text id="kixply"
.project/reports/
```

---

## 16. Forbidden Patterns

Codex must not introduce:

```text id="rh344e"
multi-agent supervisor architecture
planner-worker split
model router
workflow DAG as core runtime
external memory repo
unapproved vector database
unapproved GraphRAG
unapproved autonomous deployment
silent dependency installation
unreviewed architecture rewrite
```

Unless the user explicitly approves a change to the project architecture.

---

## 17. Final Operating Rule

Codex should behave as:

```text id="3pwujy"
single execution agent
inside a governed project workspace
using Harness OS skills
with Git as the source of truth
```

Harness OS provides:

```text id="sp4zvt"
workspace
context
state
skills
governance
verification
observability
delivery
```

Codex provides:

```text id="wowboa"
reasoning
coding
review
execution
task completion
```
```
