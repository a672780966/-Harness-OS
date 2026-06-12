# Codex Output Template

Each finding must use the following format:

```markdown
## Finding ID

- Severity: P0 / P1 / P2 / P3
- Module:
- File:
- Evidence:
- Risk:
- Recommended Fix:
- Requires Code Change: yes/no
- Blocks v1.0.0-rc.1: yes/no
- Related Design Doc:
- Related Test:
```

## Severity Definitions

| Level | Definition | Examples |
|---|---|---|
| **P0** | Blocks RC. Must fix before release. | Security bypass, secret leak, delivery bypasses verification, CLI JSON contract broken, tests cannot run. |
| **P1** | Should fix before v1.0.0 final but does not block RC. | Timeout/cancellation, approval UX, context refresh, report completeness. |
| **P2** | Deferrable. Usually belongs to Thick Harness or UX enhancement. | Symlink escape, multi-project, archive/restore. |
| **P3** | Documentation, naming, readability, or low-risk improvements. | Typo in comments, minor formatting, missing edge case in test. |

## Expected Output Files

| File | Content |
|---|---|
| `CODEX_FULL_SOURCE_AUDIT.md` | Full source-level audit with all findings |
| `CODEX_SECURITY_AUDIT.md` | Security-focused audit (governance, secrets, path escape) |
| `CODEX_RC_READINESS_REVIEW.md` | RC readiness verdict based on checklist |
| `CODEX_FIX_RECOMMENDATIONS.md` | Prioritized fix recommendations |
