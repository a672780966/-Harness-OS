# Migration Log

This log records the narrative cleanup that refocuses the public repository from a
broad Harness OS / Mobius vision into a focused **Captain Code** product repository.

Principles:

- **Nothing is deleted.** Broad-vision material is preserved under `archive/` (or a
  private/local vault) and recorded here.
- **Code is kept.** This is a *narrative* cleanup, not a code refactor. The runtime
  implementation stays public; only the public-facing story is downgraded.
- **Protocol objects stay generic.** `TaskEnvelope`, `Invocation`, `Artifact`,
  `Evidence`, `Review`, `GateDecision`, `AuditEvent`, `ReturnRecord`, `Trace`,
  `Policy`, and `Hermes` are not renamed into code-only terms.

Status legend: **DONE** = action taken · **TODO** = action still required.

---

## Rewritten

| Original path  | New path                                            | Reason                                                                 | Remains public | Status |
| -------------- | --------------------------------------------------- | ---------------------------------------------------------------------- | -------------- | ------ |
| `README.md`    | `README.md` (rewritten) + `archive/mobius_theory/README_mobius_vision_v1.md` (original) | Replace Mobius "Temporal Governance" hero with focused Captain Code framing; preserve original in archive. | Yes (new) / No (original) | TODO |
| `README.zh.md` | `README.zh.md` (rewrite) + archive original         | Translation of the broad vision; rewrite to match new README.          | Yes (new)      | TODO |
| `README.ja.md` | `README.ja.md` (rewrite) + archive original         | Same as above.                                                         | Yes (new)      | TODO |
| `README.ko.md` | `README.ko.md` (rewrite) + archive original         | Same as above.                                                         | Yes (new)      | TODO |
| `AGENTS.md`    | `AGENTS.md` (trimmed)                                | Keep as host pack, but remove broad-vision / four-layer framing. Added Current Execution Role Mapping. | Yes            | DONE |
| `CLAUDE.md`    | `CLAUDE.md` (trimmed)                                | Trimmed to Captain Code implementation-worker instructions; removed Harness OS framing. | Yes            | DONE |

## Created

| New path                      | Reason                                                        | Remains public | Status |
| ----------------------------- | ------------------------------------------------------------ | -------------- | ------ |
| `docs/quickstart.md`          | Minimal install + first-run guide.                           | Yes            | DONE   |
| `docs/workflow.md`            | Protocol objects and the execution loop.                     | Yes            | DONE   |
| `docs/architecture-lite.md`   | Small architecture, components and boundaries only.          | Yes            | DONE   |
| `docs/hermes-loop-lock.md`    | Hermes runner rules and safety locks.                        | Yes            | DONE   |
| `archive/README.md`           | Index and policy for the archived broad-vision material.     | Yes (index)    | DONE   |
| `migration_log.md`            | This file.                                                   | Yes            | DONE   |

## Moved to archive (out of public narrative)

| Original path                              | New path                              | Reason                                                       | Remains public | Status |
| ------------------------------------------ | ------------------------------------- | ----------------------------------------------------------- | -------------- | ------ |
| `harness_os_docs/`                         | `archive/harness_os_legacy/`          | Harness OS full vision material.                            | No             | TODO |
| `docs/v1_3_main_integration_seal.md`       | `archive/old_docs/`                   | Internal seal manifest / release history.                  | No             | TODO |
| `docs/v1_2_alpha_final_seal_manifest.md`   | `archive/old_docs/`                   | Internal seal manifest.                                    | No             | TODO |
| `docs/v1_2_alpha_command_reference.md`     | `archive/old_docs/`                   | Superseded by `docs/quickstart.md`.                        | No             | TODO |
| `docs/public_safe_evidence_strategy.md`    | `archive/old_docs/`                   | Internal evidence/ops strategy.                            | No             | TODO |
| `docs/public_safe_tag_mapping.md`          | `archive/old_docs/`                   | Internal tag/ops mapping.                                  | No             | TODO |
| `docs/large_evidence_archive_manifest.md`  | `archive/old_docs/`                   | Internal evidence archive manifest.                        | No             | TODO |
| `docs/github_cloud_simulation_report.md`   | `archive/old_docs/`                   | Internal ops report.                                       | No             | TODO |
| `Harness-OS-P0-Fix-Requirements/`          | `archive/old_docs/`                   | Internal fix-requirement history.                          | No             | TODO |
| `Harness-OS-Third-Round-Fix-Requirements/` | `archive/old_docs/`                   | Internal fix-requirement history.                          | No             | TODO |
| `fix-reports/`                             | `archive/old_docs/`                   | Internal fix reports.                                      | No             | TODO |
| `assets/brand/mobius-homepage-hero-v1.png` | `archive/future_vision/`              | Mobius "Temporal Governance" hero; remove from public README. | No          | TODO |
| `BENCHMARK.md`                             | `archive/research_notes/`             | Benchmark/eval material; keep public docs minimal.         | No (optional)  | TODO |
| `EVALUATION_PLAN.md`                       | `archive/research_notes/`             | Evaluation planning; keep public docs minimal.             | No (optional)  | TODO |

## Kept public (implementation / operational)

| Path                  | Reason                                                            | Remains public | Status |
| --------------------- | ---------------------------------------------------------------- | -------------- | ------ |
| `harness/`            | Runtime implementation. Narrative cleanup does not remove code.  | Yes            | KEEP |
| `src/`                | Implementation.                                                  | Yes            | KEEP |
| `schemas/`            | Protocol schemas.                                                | Yes            | KEEP |
| `templates/`          | Templates used by the runtime.                                  | Yes            | KEEP |
| `tests/`              | Test suite.                                                     | Yes            | KEEP |
| `.harness/`           | Local runtime config.                                           | Yes            | KEEP |
| `.claude/`            | Host pack config.                                               | Yes            | KEEP |
| `.github/workflows/`  | CI.                                                             | Yes            | KEEP |
| `.project/state/`     | Local state.                                                    | Yes            | KEEP |
| Build/config files    | `package.json`, `tsconfig*.json`, `pnpm-*.yaml`, `eslint.config.js`, `vitest.config.ts`, `.prettierrc`, `.gitignore`, `.gitattributes`. | Yes | KEEP |

---

## Embedded-content note

Some kept files still contain broad-vision language inline (for example, four-layer
"Temporal Governance", Canon / 矩 enterprise governance, StarMap long-term vision,
OKF / RAG theory, AIF / Spatial / Trace future product lines). When trimming a kept
file, move the excised sections into the matching `archive/` subfolder rather than
deleting them, and add a row to the **Rewritten** table above.

## Optional: private vault instead of in-repo archive

If you prefer the broad-vision material out of the public repo entirely, move it to a
private/local vault instead of `archive/` and record the destination here (e.g.
`vault://mobius/...`). The rule is the same: record every move; delete nothing.
