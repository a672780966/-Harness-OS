# AGENTS.md

## 1. Project Identity

Project Name: harness-os
Project Type: agent-harness
Primary Language: TypeScript
Runtime: Node.js
Package Manager: pnpm

Repository Role:
This repository contains Harness OS itself — the Codex-first Project Operating System.
Harness OS is built by Codex, for Codex.

### Audit Constraints

Current Phase: v1.0.0-rc.2 Thin Harness Release Candidate

Do:
  Read docs before changing code.
  Run typecheck and tests before reporting readiness.
  Use `docs/audit/` templates for audit output.
  Treat governance, secrets, verification, delivery, and config as high-risk areas.

Do Not:
  Do not start Thick Harness.
  Do not add new skills.
  Do not modify accepted ADRs without explicit approval.
  Do not commit runtime artifacts.
  Do not push tags unless explicitly requested.

## 2. Project Goals

This project exists to:
- Build a complete Project Operating System for Codex
- Enable Codex to create, maintain, verify, and deliver real engineering projects
- Provide governed, observable, recoverable project execution

## 3. Architecture Rules

1. Single Agent — Codex is the only execution agent
2. Single Model — one primary model for all reasoning
3. Skills are tools, not agents
4. Git is the long-term source of truth
5. Workspace first — state lives in .project/, not chat history

## 4. Development Commands

Install dependencies: pnpm install
Run development: pnpm dev
Build: pnpm build
Run tests: pnpm test
Run lint: pnpm lint
Run typecheck: pnpm typecheck

## 5. Testing and Verification

Required verification order:
1. typecheck
2. unit tests
3. integration tests
4. build

## 6. Repository Structure

```
harness-os/
  src/
    cli/          — CLI entry point and command handlers
    project/      — Project Manager
    task/         — Task Manager
    decision/     — Decision Manager
    context/      — Context Engineering
    skills/       — MCP Skill implementations
    governance/   — Policy Engine and Approval Gate
    verification/ — Verification System
    observability/— Event Log and Reports
    delivery/     — Delivery Pipeline
    state/        — Checkpoint and State System
  tests/          — Unit, Integration, E2E tests
  schemas/        — JSON schemas
  templates/      — AGENTS.md, ADR templates
  docs/           — Documentation
```
