# Release Checklist — Harness OS v1.0.0

**Commit SHA:** `e6ccb4a15fcc9b4885c313715cd2b52d906ed203`  
**Commit Date:** 2026-06-15  
**Pre-tag Status:** All P0 closed, re-audit fixes applied, audit reports updated  

---

## Phase 1: Human Review (Pre-Tag)

- [x] Review `CODEX_FIX_COMPLETION_REAUDIT.md` for re-audit findings
- [x] Review `THIRD_ROUND_FULL_AUDIT.md` for completeness
- [x] Review `THIRD_ROUND_SECURITY_VERIFICATION.md` for security posture
- [x] Review `V1_READINESS_REVIEW.md` for gate status
- [x] Confirm no business logic changes outside scope
- [x] Confirm old `v1.0.0-rc.1` tag is not moved

## Phase 2: Create Tag (executed 2026-06-15)

```powershell
# Tag created — not pushed (pending remote access)
git tag -a v1.0.0 -m "Harness OS v1.0.0 — final release"

# Manual action required: push to remote
# git push origin v1.0.0
```

## Phase 3: Post-Tag Verification (executed 2026-06-15)

- [x] `git tag --list` shows `v1.0.0`
- [x] `git describe --tags` returns `v1.0.0`
- [x] `node dist/index.js --version` returns `1.0.0`
- [ ] GitHub Actions CI passes on the tagged commit

## Phase 4: Release Artifacts

- [x] Build produces `dist/index.js` (ESM, 40.98 KB)
- [x] Build produces `dist/index.d.ts` (TypeScript declarations)
- [ ] Release notes drafted from audit reports
- [ ] Binary/package published (if applicable)

## Phase 5: Post-Release

- [ ] Monitor CI for any environment-specific failures
- [ ] Verify clean clone install: `corepack enable && pnpm install --frozen-lockfile`
- [ ] Update any downstream consumers

---

## Quick Reference

```powershell
# Tag created: v1.0.0 (commit e6ccb4a)
# Not yet pushed — run manually:
# git push origin v1.0.0
```
