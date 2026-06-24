# Public-Safe Evidence Strategy

## Why GitHub Rejected Tag Push

On 2026-06-24, `git push --tags origin v1.2/engineering-copilot-ux` was rejected by GitHub's pre-receive hook:

```
remote: error: File dist/swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz
         is 373.18 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: GH001: Large files detected.
```

The file is a SWE-bench Mini Pilot evidence archive containing test results, diffs, logs, and evaluation artifacts from the v1.1.1 milestone. It lives in Git history reachable from 17 local tags.

## Why Not Rewrite History

| Option | Rejected | Reason |
|--------|:--------:|--------|
| `git filter-branch` | ❌ | Destructive — rewrites commit SHA for every descendant. Invalidates all local tags and worktrees. |
| `git filter-repo` | ❌ | Same destructive effect. Requires force push, breaks collaboration. |
| Git LFS migrate | ❌ | Requires rewriting history and force push. LFS not configured on this repo. |
| `git push --force` | ❌ | Silently drops blocked tags, confuses collaborators. |

**Decision**: Keep local history intact. The large file is a legitimate evidence artifact, not an accidental commit. It should be preserved locally and published via GitHub Releases instead.

## Local Sealed Tag vs Remote Public-Safe Tag

| Aspect | Local Sealed Tag | Remote Public-Safe Tag |
|--------|:----------------:|:----------------------:|
| **Purpose** | Trusted audit trail | Publicly accessible milestone |
| **Content** | Full evidence chain including large archives | Sanitized — manifests + sha256 only |
| **Location** | Local only | GitHub remote |
| **Git history** | Original (includes large blobs) | Sanitized (large blobs excluded) |
| **Pushed** | No (blocked by GH limit) | Yes |
| **SHA256 included** | Optional | Mandatory (in manifest docs) |

## Large Archive Treatment

```
dist/swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz (373.18 MB)
→ Remove from Git history for public-facing refs
→ Publish sha256 + source_commit + manifest in docs/
→ Upload archive to GitHub Release Asset or external storage
→ Local sealed tags retain full history
```

## Recommended Remote Publication Structure

```
GitHub Repository: a672780966/-Harness-OS
├── main branch              ← clean tree, no large blobs
├── v1.2/engineering-copilot-ux  ← feature branch (already pushed)
├── Tags (remote):
│   ├── v1.0.0               ← already on remote
│   ├── v1.0.0-rc.1          ← already on remote
│   └── v1.1-real-loop-sealed ← pushed 2026-06-24
└── Releases (GitHub UI):
    └── v1.1.1-mini-pilot-sealed
        ├── source code (tag)
        └── swebench_evidence_f3aca38.tar.gz (Release Asset)
```

For future public-safe tags, create tags that point to commits prior to the large blob's introduction (e.g., `v1.1-real-loop-sealed` is safe because it predates the archive).

## Strategy Summary

```yaml
strategy:
  keep_local_sealed_tags: true
  do_not_rewrite_history: true
  do_not_push_blocked_tags: true
  create_public_safe_branch_or_history: later
  keep_manifests_and_sha256_in_git: true
  move_large_archives_to_release_assets_or_external_storage: true
```

## Next Steps for Main Branch Publication

1. Create a `main` or release branch from the latest clean commit (after `v1.1-real-loop-sealed`).
2. Apply sanitized patches from later milestones, excluding large binary files.
3. Tag public-safe checkpoints with `-public` suffix.
4. Upload large evidence archives as GitHub Release Assets.
5. Update this strategy doc with final decisions.
