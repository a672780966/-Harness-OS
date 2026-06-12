# Codex Allowed Commands

## Build & Test

```bash
pnpm install
pnpm tsc --noEmit
pnpm test
pnpm build
```

## Git (read-only)

```bash
git status --short
git diff --stat
git diff
git log --oneline -n 20
git tag --list
```

## Harness Self-Check

```bash
harness status
harness check
harness config --json
harness skills list
harness decision list
```

## Notes

- If a command is blocked by hooks, record the hook issue. Do not bypass security policy.
- If a destructive command is needed, use dry-run, mock, fixture, or static audit only.
- Do not run commands that modify files, git state, or project structure.
