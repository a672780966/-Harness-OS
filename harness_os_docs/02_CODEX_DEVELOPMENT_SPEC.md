# Harness OS — Codex 开发规范（完整版）

**Version:** 1.0  
**Project Codename:** Harness OS  
**定位:** Codex First Project Operating System

---

# 1. 项目愿景（Vision）

构建一个面向 Codex 的工程级 Agent Harness。

目标不是：

```text id="wjx24a"
聊天机器人
Workflow平台
Dify替代品
Multi-Agent平台
RAG平台
```

目标是：

```text id="b01gcr"
让 Codex 具备长期维护项目的能力
```

即：

```text id="12b7to"
创建项目
理解项目
执行项目
验证项目
交付项目
恢复项目
```

Harness 负责：

```text id="nhml7c"
Workspace
State
Context
Skills
Governance
Verification
Observability
Delivery
```

Codex 负责：

```text id="te5myx"
Reasoning
Planning
Coding
Execution
```

---

# 2. 核心原则

## 单 Agent

禁止：

```text id="6lak98"
Planner Agent
Research Agent
Coder Agent
Reviewer Agent
Supervisor Agent
```

允许：

```text id="59febu"
Codex
+
Skills
```

---

## 单模型

禁止：

```text id="rdm6m9"
Claude规划
Gemini搜索
Codex编码
```

允许：

```text id="bkyoad"
一个主模型
```

所有：

```text id="8r5kuy"
总结
Review
Decision
Context理解
```

均由同一模型完成。

---

## Workspace First

项目状态保存在：

```text id="pj55m0"
Workspace
Git
Project State
```

而不是：

```text id="xggc1s"
聊天历史
```

---

## Git First

长期事实来源：

```text id="83kqj6"
Git Repository
```

而不是：

```text id="0xmbfz"
Vector DB
```

---

## MCP Native

Skills 属于 Harness。

不是外挂系统。

---

# 3. 技术栈

## Runtime

```text id="q56nkw"
Node.js 22+
TypeScript 5+
```

原因：

```text id="t4gda6"
CLI生态成熟
MCP生态成熟
Git集成方便
跨平台
```

---

## CLI

```text id="4emrbk"
Commander
Ink
```

---

## Backend Runtime

```text id="divyf7"
Node Runtime
```

---

## State

```text id="kkxxcv"
SQLite
JSON
Filesystem
```

用途：

```text id="z9q4kh"
Sessions
Task State
Project State
Checkpoints
```

---

## Code Analysis

```text id="r4jc78"
Tree-Sitter
Ripgrep
```

用途：

```text id="0ydb77"
Repository Map
Symbol Discovery
Context Discovery
```

---

## Git

```text id="0r0316"
simple-git
Git CLI
```

---

## GitHub

```text id="lypbkv"
GitHub MCP
GitHub API
```

---

## Testing

```text id="f378gz"
Vitest
Playwright
```

---

## Validation

```text id="a9816i"
Zod
```

---

## Logging

```text id="g6bg0q"
Pino
```

---

# 4. 系统架构

```text id="ck4pg0"
Harness Runtime
│
├── Project Manager
│
├── Agent Runtime Adapter
│
├── Context System
│
├── State System
│
├── MCP Skill Layer
│
├── Governance System
│
├── Verification System
│
├── Observability System
│
└── Delivery System
```

---

# 5. Workspace Architecture

## 项目结构

```text id="1le0u4"
repo/
│
├── AGENTS.md
├── .project/
│   ├── state/
│   ├── tasks/
│   ├── decisions/
│   ├── reports/
│   ├── checkpoints/
│   ├── sessions/
│   └── context/
│
├── src/
├── docs/
├── tests/
└── ...
```

---

## Workspace 生命周期

```text id="taamlr"
Create
Open
Run
Checkpoint
Resume
Archive
Restore
```

---

# 6. Project Manager

负责：

```text id="7iuxck"
Project Creation
Project Loading
Project Recovery
Project Migration
Project Configuration
```

---

## Commands

```bash id="q4lnpw"
harness create
harness open
harness run
harness resume
harness archive
harness restore
```

---

# 7. AGENTS.md Protocol

必须存在。

Agent进入项目第一步：

```text id="gkopzl"
读取 AGENTS.md
```

---

## 内容

```text id="pcndya"
Project Goal
Architecture Rules
Coding Standards
Run Commands
Test Commands
Approval Rules
Available Skills
Context Rules
```

---

# 8. Context System

整个系统核心。

---

## 输入

```text id="2n98ca"
AGENTS.md

Project State

Current Task

Git Diff

Recent Tasks

Repository Map

Test Results
```

---

## 输出

```text id="agk5le"
Context Pack
```

---

## Context Pack

```text id="j3lvjn"
Task

Project Facts

Current State

Relevant Files

Relevant Decisions

Recent Changes

Constraints

Available Skills
```

---

## Responsibilities

```text id="118nxw"
Discovery
Selection
Compression
Assembly
```

---

# 9. State System

参考：

```text id="k91mcn"
Claude Sessions
OpenAI Sessions
```

---

## State Tree

```text id="0jff5i"
Project
│
├── Sessions
├── Tasks
├── Decisions
├── Checkpoints
└── Reports
```

---

## Session

记录：

```text id="ofrpaq"
Current Task
Execution History
Context Summary
State Snapshot
```

---

## Checkpoint

记录：

```text id="lz88ue"
Git State
Task State
Context State
Skill State
```

支持：

```text id="cdr4qe"
Rollback
Resume
Recovery
```

---

# 10. MCP Skill Layer

Skill = 能力

不是 Agent。

---

## Filesystem Skill

```text id="dkenbx"
Read
Write
Move
Delete
Create
```

---

## Shell Skill

```text id="0umdow"
Command Execution
Build
Test
Install
```

---

## Git Skill

```text id="bh66r8"
Status
Diff
Commit
Branch
Merge
Revert
```

---

## GitHub Skill

```text id="ensc93"
PR
Issue
Review
Release
```

---

## Browser Skill

```text id="cwhtz9"
Documentation Reading
Issue Analysis
Research
```

---

## Repo Scanner Skill

```text id="xoktdi"
Dependency Discovery
Code Mapping
Symbol Analysis
```

---

## Database Skill

```text id="noy5lf"
SQLite
Postgres
MySQL
```

---

# 11. Governance System

负责：

```text id="ylq6yu"
Permissions
Approvals
Security
Policies
```

---

## Approval Gate

必须审批：

```text id="qbbmqq"
Delete Files
Modify AGENTS.md
Modify Architecture
Deploy
Push Main
```

---

## Secret Protection

禁止：

```text id="oowuqi"
Key Leakage
Credential Leakage
Token Logging
```

---

## Budget Control

限制：

```text id="83ac8k"
Token Budget
Tool Budget
Execution Budget
```

---

# 12. Verification System

任何任务结束必须验证。

---

## Lint

```text id="0rdtre"
ESLint
Ruff
golangci-lint
```

---

## Typecheck

```text id="gd8egc"
TSC
Mypy
```

---

## Tests

```text id="mxpcp9"
Unit
Integration
E2E
```

---

## AI Review

检查：

```text id="j0ygwc"
Risk
Consistency
Coverage
Architecture Compliance
```

---

# 13. Observability System

参考：

```text id="bhv1th"
OpenAI Tracing
Anthropic Harness Logs
```

---

## Event Stream

记录：

```text id="0o1vcy"
Task Start
Task End
Tool Calls
File Changes
Verification
Approvals
```

---

## Trace

保存：

```text id="9lbv8w"
Run Timeline
Tool Timeline
Context Timeline
```

---

## Replay

支持：

```text id="3t18ir"
Replay Run
Replay Task
Replay Failure
```

---

## Run Report

自动生成：

```text id="5ou2zr"
Goal
Changes
Tests
Risks
Next Steps
```

---

# 14. Delivery System

负责：

```text id="safin9"
Commit
PR
Release
Deploy
Rollback
```

---

## Commit

自动生成：

```text id="r97mvd"
Conventional Commit
```

---

## PR

自动生成：

```text id="b5me61"
Summary
Files Changed
Tests
Risks
```

---

## Release

生成：

```text id="0np80r"
Release Notes
Changelog
```

---

## Deploy

统一入口：

```bash id="tfn13a"
harness deploy
```

---

# 15. Project Memory（作为 Context 子系统）

注意：

```text id="5ywn31"
Memory 不是独立产品
```

属于：

```text id="3it2de"
Context System
```

---

## 存储位置

```text id="lkipgk"
.project/
```

---

## 内容

```text id="nyyz34"
Project Facts
Tasks
Decisions
Reports
Checkpoints
```

---

## 不使用

```text id="kkaokv"
独立 Memory Repo
独立 Knowledge Repo
独立 Vector Platform
```

---

# 16. 开源项目映射

## Claude Code

借鉴：

```text id="x7rc90"
Workspace
Permissions
Tool Runtime
Sessions
```

不复制：

```text id="cv3x3u"
产品实现
```

---

## Claude Agent SDK

借鉴：

```text id="alzken"
Hooks
MCP
Tool Runtime
```

---

## OpenAI Agents SDK

借鉴：

```text id="nmi45w"
Sessions
Tracing
Guardrails
Tools
```

---

## iii Harness

借鉴：

```text id="w2ezhi"
Harness Runtime
Harness = Backend
Worker Architecture
```

---

## Aider

借鉴：

```text id="a11glw"
Git First
Repo First
Single Agent
```

---

## Continue

借鉴：

```text id="60cral"
Workspace Awareness
Codebase Discovery
```

---

## OpenCode

借鉴：

```text id="4tvkc2"
Terminal Integration
Workspace Runtime
```

---

## LangGraph

仅借鉴：

```text id="q5u2j7"
State Machine
Checkpoint
Persistence
```

禁止：

```text id="hrg4rx"
Multi-Agent Graph
Supervisor Pattern
```

---

# 17. 非目标（Non Goals）

禁止进入范围：

```text id="kxuqfd"
Multi-Agent

Agent Society

Workflow DAG

Complex Router

Model Router

Vector Platform

GraphRAG

Auto Research Network

Prompt Marketplace
```

---

# 18. 验收标准（Acceptance Criteria）

## P0 Runtime

能够：

```text id="ph5u12"
Create Project
Open Project
Run Task
Resume Task
Recover Task
```

---

## P0 Context

能够：

```text id="e19egy"
Build Context Pack
Recover Context
Compress Context
```

---

## P0 State

支持：

```text id="5xbriy"
Session
Checkpoint
Resume
Rollback
```

---

## P0 Skills

支持：

```text id="bqtpgs"
Filesystem
Shell
Git
GitHub
Browser
RepoScanner
Database
```

---

## P0 Governance

支持：

```text id="hduxdn"
Permissions
Approvals
Secret Protection
Budget Control
```

---

## P0 Verification

支持：

```text id="rqxhyw"
Lint
Typecheck
Tests
Review
```

---

## P0 Observability

支持：

```text id="k642rb"
Logs
Traces
Replay
Reports
```

---

## P0 Delivery

支持：

```text id="mdr2ft"
Commit
PR
Release
Deploy
Rollback
```

---

# 最终定义

```text id="gjdwsa"
Harness OS
=
Workspace
+
Context
+
State
+
Skills
+
Governance
+
Verification
+
Observability
+
Delivery
```

```text id="cdnuwv"
Codex
=
唯一执行 Agent
```

最终目标：

```text id="92wwjx"
把 Codex 从代码生成器提升为长期项目执行者，
而 Harness OS 成为它的 Project Operating System。
```
