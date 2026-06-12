# Codex Forbidden Actions

The following actions are explicitly forbidden during audit:

| # | Action | Reason |
|---|---|---|
| 1 | Start Thick Harness | Out of RC scope |
| 2 | Add GitHub Skill | Thick Harness |
| 3 | Add Browser Skill | Thick Harness |
| 4 | Add Database Skill | Thick Harness |
| 5 | Add Replay | Thick Harness |
| 6 | Add multi-project registration | Thick Harness |
| 7 | Add migration system | Thick Harness |
| 8 | Auto-modify accepted ADRs | Requires human approval |
| 9 | Commit secrets of any kind | Security policy |
| 10 | `git add .project/context` | Runtime artifact, not for git |
| 11 | `git add .project/checkpoints/` | Runtime artifact, not for git |
| 12 | `git add .project/reports/events/` or `traces/` | Runtime artifact, not for git |
| 13 | Force push | Destructive |
| 14 | Push to main unless explicitly requested | Governance policy |
| 15 | Create new tags unless explicitly requested | Release control |
| 16 | Turn P2/P3 findings into large refactoring | Scope creep |
| 17 | Mark Thick Harness as completed | False status |
