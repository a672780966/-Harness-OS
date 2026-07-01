# v1.3 Main Integration Seal

## PR

- **PR**: https://github.com/a672780966/-Harness-OS/pull/1
- **Merge method**: Create a merge commit
- **Merge commit**: `b4817c0`
- **Main HEAD**: `b4817c0`
- **Feature branch HEAD**: `b9221a1`

## Integration Tag

- **Tag**: `v1.3-main-integration`

## Test Results

| Suite | Results |
|-------|:-------:|
| Copilot tests | **616 passed** |
| Full pytest | **848 passed** |

## Tag Policy

### Pushed (safe) tags

| Tag | Status |
|:----|:------:|
| `v1.1-real-loop-sealed` | ✅ Pushed |
| `v1.3-public-safe-evidence-plan` | ✅ Pushed |
| `v1.3.1-pr-draft-assistant` | ✅ Pushed |
| `v1.3-main-integration` | ✅ Pushed |

### Blocked local tags (17)

These sealed tags remain local-only because their reachable history includes a 373.18 MB SWE-bench evidence archive that exceeds GitHub's 100 MB blob limit.

```
v1.1.1-mini-pilot-sealed        v1.2-alpha-kernel-complete
v1.2-alpha-ux-complete          v1.2-alpha-integration-complete
v1.2-alpha-phase4-shell-complete v1.2-alpha-monitor-complete
v1.2-alpha-pr-pack-complete     v1.2-alpha-provider-guard-complete
v1.2-alpha-agent-state-complete v1.2-alpha-live-dashboard-complete
v1.2-alpha-local-mvp-sealed     v1.2-alpha-final-sealed
v1.2.1-dogfood-stabilized       v1.3-foundation-config-complete
v1.3-workspace-hygiene-complete v1.3-pre-merge-clean-complete
v1.3-planning-cross-project-runtime
```

## Large Evidence Archive

```yaml
archive: dist/swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz
size: 373.18 MB
sha256: de88b255287899286ba13c74479d92e500a14a42e749835c1516f77c26c4f6c1
reason: GitHub 100MB blob limit
status: preserved locally, not pushed
strategy_doc: docs/public_safe_evidence_strategy.md
```

## Sealed Evidence

- `.harness/evaluations/` — **unchanged** ✅
- Sealed Mini Pilot evidence — **unchanged** ✅
