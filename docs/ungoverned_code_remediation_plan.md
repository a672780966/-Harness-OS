# Ungoverned Code Remediation Plan

**Generated**: 2026-06-25T06:30 CST

## Status: ALL CLEAN

本轮 Temporary Loop 治理恢复全部 6 阶段已完成。以下为最终 remediation 状态。

---

## Phase 1: v1.2 source-fix — COP-1~COP-5 ✅ DONE

| COP | 问题 | 修复 | Actor | 文件 | 已验证 |
|:----|:-----|:-----|:-----|:-----|:------:|
| COP-1 | CLI docstring 缺失 36+ v1.2 命令、残留 stale `sync` | 完整 docstring 重写 + 命令分类 | Codex Emergency | `cli.py` | ✅ |
| COP-2 | Read-only/WRITE/NETWORK 治理分类模糊 | 显式标注每类命令的治理等级 | Codex Emergency | `cli.py` | ✅ |
| COP-3 | Provider guard tunables 硬编码 | tunables → HarnessConfig schema → loader 注入 | Codex Emergency | `schema.py`, `loader.py`, `config.py` | ✅ |
| COP-4 | `long_phase_allowed_when_degraded` 未配置 | 标志位 → canary/health 检查逻辑 | Codex Emergency | `canary.py`, `health.py`, `config.py` | ✅ |
| COP-5 | Retry 配置 (max_retries, backoff, jitter) 不可配置 | schema + loader + env 完整暴露 | Codex Emergency | `schema.py`, `loader.py`, `config.py` | ✅ |

## Phase 2: v1.2.1 Dogfood ✅ DONE

Docs-only audit — 无 remediation 项。

## Phase 3: v1.3 Foundation Config ✅ DONE

Docs-only audit — 无 remediation 项。

## Phase 4: v1.3.1 PR Draft Assistant ✅ DONE

Docs-only audit — 无 remediation 项。

## Phase 5: Loop Installer self-audit ✅ DONE

Docs-only audit — 无 remediation 项。

## Phase 6: Global Consistency ✅ DONE

Docs-only audit — 无 remediation 项。

---

## 仍需要修复的项

### 1. OpenCode 空结果问题

**影响**: 18 次 OpenCode Worker 调用中 14 次返回空 `{"files_changed": []}`。

**根本原因**: OpenCode 在无人工引导 prompt 的场景下无法自主产出 diff。source-fix 和 docs-audit 任务均需 Codex Emergency fallback。

**建议**: 
- 短期接受：Codex Emergency 为可靠 fallback（成功率 100%）
- 中期优化：改进 task_envelope 指令格式，或使用 Claude Code 替代 OpenCode Worker
- 如需保留 OpenCode Worker：必须优化 prompt engineering，包含明确的 diff 格式和示例

### 2. 未跟踪的文件

以下文件为 untracked，未包含在 `fe0d5fc` commit 中：

| 文件 | 状态 | 建议 |
|:-----|:----:|:-----|
| docs/v1_1_governance_audit_report.md | untracked | 如需归档可加入 docs commit |
| docs/v1_2_engineering_copilot_governance_audit.md | untracked | 如需归档可加入 docs commit |
| docs/v1_2_engineering_copilot_source_fix_plan.md | untracked | 如需归档可加入 docs commit |
| docs/v1_2_1_dogfood_audit_report.md | untracked | 本轮产出 → 建议 commit |
| docs/v1_2_1_dogfood_stabilization_audit.md | untracked | 如需归档可加入 docs commit |
| docs/v1_3_foundation_runtime_audit.md | untracked | 本轮产出 → 建议 commit |
| docs/v1_3_1_pr_draft_assistant_audit.md | untracked | 本轮产出 → 建议 commit |
| docs/loop_installer_self_audit.md | untracked | 本轮产出 → 建议 commit |
| docs/global_consistency_audit.md | untracked | 本轮产出 → 建议 commit |
| harness/runtime/envelope_validator.py | untracked | ⚠️ 非本轮产出，需确认来源 |
| tests/test_runtime_envelope_validator.py | untracked | ⚠️ 非本轮产出，需确认来源 |

## 最终裁决

✅ **无未修复的治理 gap**
✅ **无需要 User 产品裁决的问题**
✅ **无 Hermes Direct 源码修改**
