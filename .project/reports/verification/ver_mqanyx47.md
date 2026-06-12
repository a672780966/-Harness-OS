# Verification Report: ver_mqanyx47

**Task:** (no task)
**Date:** 2026-06-12T08:27:52.999Z
**Status:** PARTIAL

## Summary

| Metric | Value |
|--------|-------|
| Passed | 6 |
| Failed | 4 |
| Skipped | 3 |
| Total | 13 |
| Duration | 421.2s |

## Step Results

| # | Name | Type | Status | Exit Code | Duration |
|---|------|------|--------|-----------|----------|
| 1 | lint | lint | passed | 0 | 1.2s |
| 2 | typecheck | typecheck | passed | 0 | 3.5s |
| 3 | test | unit-test | passed | 0 | 174.5s |
| 4 | test:unit | unit-test | passed | 0 | 133.2s |
| 5 | dev | test | failed | 1 | 2.0s |
| 6 | test:coverage | test | skipped | - | 0.0s |
| 7 | test:watch | test | skipped | - | 0.0s |
| 8 | test:integration | integration-test | passed | 0 | 97.9s |
| 9 | build | build | skipped | - | 0.0s |
| 10 | test:e2e | e2e-test | failed | 1 | 1.2s |
| 11 | install | install | passed | 0 | 7.7s |
| 12 | format | format-check | failed | 1 | 0.0s |
| 13 | format:check | format-check | failed | 1 | 0.0s |

## Failures

### dev (pnpm tsx src/cli/index.ts)

```
Usage: harness [options] [command]

Harness OS - Codex-first Project Operating System

Options:
  -V, --version                    output the version number
  --json                           JSON output mode
  --quiet                          Quiet output mode
  --no-color                       Disable color output
  --log-level <level>              Log level (debug|info|warn|error)
  -h, --help                       display help for command

Commands:
  create [options] <project-name>  Create a new Harness OS project
  open <repo-path>                 Open an existing project
  init                             Initialize Harness OS in an existing project
  repair                           Repair missing or invalid project structure
  check                            Check AGENTS.md validity
  run [options] <task>             Execute a task
  resume <run-id>                  Resume a paused or interrupted run
  status                           Show current project status
  verify [opt
```

### test:e2e (vitest run tests/e2e)

```

 RUN  v4.1.8 C:/Users/Administrator/Desktop/Harness os


```

```
No test files found, exiting with code 1

filter: tests/e2e
include: tests/**/*.test.ts
exclude:  node_modules, dist


```

### format (prettier --write "src/**/*.ts")

```
'prettier' �����ڲ����ⲿ���Ҳ���ǿ����еĳ���
���������ļ���

```

### format:check (prettier --check "src/**/*.ts")

```
'prettier' �����ڲ����ⲿ���Ҳ���ǿ����еĳ���
���������ļ���

```


## Risks

- Verification failed: dev (pnpm tsx src/cli/index.ts)
- Verification failed: test:e2e (vitest run tests/e2e)
- Verification failed: format (prettier --write "src/**/*.ts")
- Verification failed: format:check (prettier --check "src/**/*.ts")
