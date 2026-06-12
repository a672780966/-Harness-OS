# RC2 Release Checklist — Harness OS v1.0.0-rc.2

**Pre-commit SHA:** `2f6be41853e3abdbd9a9f3847c8a555a4b672cd1`  
**Pre-commit Date:** 2026-06-12  
**Pre-tag Status:** All P0 closed, audit reports committed  

---

## Phase 1: Human Review (Pre-Tag)

- [ ] Review `THIRD_ROUND_FULL_AUDIT.md` for completeness
- [ ] Review `THIRD_ROUND_SECURITY_VERIFICATION.md` for security posture
- [ ] Review `RC2_READINESS_REVIEW.md` for gate status
- [ ] Confirm no business logic changes outside scope
- [ ] Confirm old `v1.0.0-rc.1` tag is not moved

## Phase 2: Create Tag

After human approval, run:

```powershell
# Fetch latest
git fetch origin main

# Verify again
git status --short
pnpm.cmd typecheck
pnpm.cmd test
pnpm.cmd build

# Create signed tag
git tag -a v1.0.0-rc.2 -m "Harness OS v1.0.0-rc.2 — third-round audit fixes"

# Push tag only (not commits — commits are already pushed)
git push origin v1.0.0-rc.2
```

## Phase 3: Post-Tag Verification

- [ ] `git tag --list` shows `v1.0.0-rc.2`
- [ ] `git describe --tags` returns `v1.0.0-rc.2`
- [ ] `node dist/index.js --version` returns `1.0.0-rc.2`
- [ ] GitHub Actions CI passes on the tagged commit

## Phase 4: Release Artifacts

- [ ] Build produces `dist/index.js` (ESM, 34.6 KB)
- [ ] Build produces `dist/index.d.ts` (TypeScript declarations)
- [ ] Release notes drafted from audit reports
- [ ] Binary/package published (if applicable)

## Phase 5: Post-Release

- [ ] Monitor CI for any environment-specific failures
- [ ] Verify clean clone install: `corepack enable && pnpm install --frozen-lockfile`
- [ ] Update any downstream consumers

---

## Quick Reference

```powershell
# Full gate check
pnpm.cmd typecheck
pnpm.cmd test --run
pnpm.cmd build
node dist/index.js --version
node dist/index.js --json config | ConvertFrom-Json
node dist/index.js --json status | ConvertFrom-Json

# Tag commands (manual — NOT YET EXECUTED)
# git tag -a v1.0.0-rc.2 -m "Harness OS v1.0.0-rc.2"
# git push origin v1.0.0-rc.2
```
