# Public-Safe Tag Mapping

> **Status**: Planning only — no public-safe tags have been created.
> All mappings below are **proposed**. Actual creation deferred until user confirms.

## Mapping Convention

| Prefix | Meaning |
|--------|---------|
| `v1.*` (no suffix) | Original sealed tag (local only, may contain large blobs) |
| `v1.*-public` | Proposed public-safe tag (sanitized, pushable to remote) |

## Tag Mapping Table

| # | Local Sealed Tag | Proposed Public Tag | Status | Notes |
|---|:----------------:|:-------------------:|:------:|-------|
| 1 | `v1.0.0` | — | ✅ Already on remote | No large blobs |
| 2 | `v1.0.0-rc.1` | — | ✅ Already on remote | No large blobs |
| 3 | `v1.1-real-loop-sealed` | — | ✅ Already on remote | Predates large blob |
| 4 | `v1.1.1-mini-pilot-sealed` | `v1.1.1-mini-pilot-sealed-public` | 🟡 Planned | First tag containing 373MB tar.gz |
| 5 | `v1.2-alpha-kernel-complete` | `v1.2-alpha-kernel-complete-public` | 🟡 Planned | |
| 6 | `v1.2-alpha-ux-complete` | `v1.2-alpha-ux-complete-public` | 🟡 Planned | |
| 7 | `v1.2-alpha-integration-complete` | `v1.2-alpha-integration-complete-public` | 🟡 Planned | |
| 8 | `v1.2-alpha-phase4-shell-complete` | `v1.2-alpha-phase4-shell-complete-public` | 🟡 Planned | |
| 9 | `v1.2-alpha-monitor-complete` | `v1.2-alpha-monitor-complete-public` | 🟡 Planned | |
| 10 | `v1.2-alpha-pr-pack-complete` | `v1.2-alpha-pr-pack-complete-public` | 🟡 Planned | |
| 11 | `v1.2-alpha-provider-guard-complete` | `v1.2-alpha-provider-guard-complete-public` | 🟡 Planned | |
| 12 | `v1.2-alpha-agent-state-complete` | `v1.2-alpha-agent-state-complete-public` | 🟡 Planned | |
| 13 | `v1.2-alpha-live-dashboard-complete` | `v1.2-alpha-live-dashboard-complete-public` | 🟡 Planned | |
| 14 | `v1.2-alpha-local-mvp-sealed` | `v1.2-alpha-local-mvp-sealed-public` | 🟡 Planned | |
| 15 | `v1.2-alpha-final-sealed` | `v1.2-alpha-final-sealed-public` | 🟡 Planned | |
| 16 | `v1.2.1-dogfood-stabilized` | `v1.2.1-dogfood-stabilized-public` | 🟡 Planned | |
| 17 | `v1.3-foundation-config-complete` | `v1.3-foundation-config-complete-public` | 🟡 Planned | |
| 18 | `v1.3-workspace-hygiene-complete` | `v1.3-workspace-hygiene-complete-public` | 🟡 Planned | |
| 19 | `v1.3-pre-merge-clean-complete` | `v1.3-pre-merge-clean-complete-public` | 🟡 Planned | |
| 20 | `v1.3-planning-cross-project-runtime` | `v1.3-planning-cross-project-runtime-public` | 🟡 Planned | |

## Implementation Approach (Deferred)

Public-safe tags should point to **sanitized commits** that exclude `dist/*.tar.gz` and other large binaries. Options:

1. **Branch-based**: Create a `public-safe/v1.2` branch from the last clean commit, cherry-pick milestone patches excluding large files.
2. **Commit-based**: For each milestone, check out the sealed tag, remove large files, commit the removal, tag as `-public`.
3. **Sparse checkout**: Tag the original commit but instruct consumers to use sparse checkout.

**Option 2** is recommended: it preserves the commit message and milestone identity while excluding large blobs. However, it still rewrites SHA for the sanitized commit (branching from the sealed commit's parent).

## What Each Public Tag Should Contain

- Source code at that milestone state
- Manifest files (`.harness/evaluations/*.json`)
- Seal evidence docs (`docs/` and `seal_manifest.md`)
- sha256 references to large archives
- **NOT** the large binary archives themselves
