# Large Evidence Archive Manifest

## Archive Identity

| Field | Value |
|-------|-------|
| archive_name | `swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz` |
| path in repo | `dist/swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz` |
| size | 373.18 MB |
| git blob SHA | `de88b255287899286ba13c74479d92e500a14a42e749835c1516f77c26c4f6c1` |
| git object ID | `4c608c2d3392bfbe5e0225f545df53f0b9117f58` |
| source commit | `f3aca38573aafe12e0bf66cfea5c4c014f93a0d5` |
| related manifest | `seal_manifest_v1.1.1_mini_pilot_sealed.md` |

> SHA256 computed from git blob: `git show v1.1.1-mini-pilot-sealed:dist/swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz | sha256sum`

## Reason for Git Rejection

GitHub's pre-receive hook enforces a **100 MB file size limit** per blob.
This archive (373.18 MB) exceeds that limit → all tags reaching this blob are blocked from push.

## Reachable Tags (17 tags — all blocked from remote)

```
v1.1.1-mini-pilot-sealed
v1.2-alpha-kernel-complete
v1.2-alpha-ux-complete
v1.2-alpha-integration-complete
v1.2-alpha-phase4-shell-complete
v1.2-alpha-monitor-complete
v1.2-alpha-pr-pack-complete
v1.2-alpha-provider-guard-complete
v1.2-alpha-agent-state-complete
v1.2-alpha-live-dashboard-complete
v1.2-alpha-local-mvp-sealed
v1.2-alpha-final-sealed
v1.2.1-dogfood-stabilized
v1.3-foundation-config-complete
v1.3-workspace-hygiene-complete
v1.3-pre-merge-clean-complete
v1.3-planning-cross-project-runtime
```

## Recommended Storage

| Option | Pros | Cons | Priority |
|--------|------|------|:--------:|
| **GitHub Release Asset** | Official GitHub hosting, attached to tag/release | Requires GitHub Release creation, 2 GB limit per release | 🥇 |
| **External object storage** | No size limits, CDN, permanent archive | Requires credentials, external dependency | 🥈 |
| **Local cold archive** | Zero cost, fully controlled | Not publicly accessible, no backup | 🥉 |

## Required Metadata (Store in Git alongside this manifest)

```yaml
sha256: de88b255287899286ba13c74479d92e500a14a42e749835c1516f77c26c4f6c1
source_commit: f3aca38573aafe12e0bf66cfea5c4c014f93a0d5
related_manifest: seal_manifest_v1.1.1_mini_pilot_sealed.md
related_local_tags:
  - v1.1.1-mini-pilot-sealed
  - v1.2-alpha-kernel-complete
  - v1.2-alpha-ux-complete
  - ... (17 total)
```

## Archive Contents (Estimated)

Based on the evidence pack structure, this archive likely contains:

- Full SWE-bench evaluation results (5 instances × 3 tiers)
- Docker evaluation logs
- Patch files and diffs
- Test output snapshots
- Seal manifest and integrity hashes
- Hermes Loop artifacts (task cards, review results, final gate)
- logs, stdout/stderr captures

## Future-proofing

To prevent similar issues in the future:

✅ `dist/*.tar.gz` added to `.gitignore` (2026-06-24)
✅ `dist/*.zip` added to `.gitignore`
✅ `*.tar.gz` / `*.tgz` / `*.zip` added to root `.gitignore`

Any future evidence archive > 10 MB should be:
1. Uploaded as a GitHub Release Asset (not committed to Git)
2. Referenced by sha256 in manifest docs
3. Stored locally under `dist/` (gitignored) for local rebuilds
