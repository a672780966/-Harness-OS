# CPIS Dogfood Regression Report — v1.2.1

**测试日期**: 2026-06-23
**基线**: `v1.2-alpha-final-sealed` (e733805)
**补丁**: v1.2.1-dogfood-stabilized

---

## 回归验证结果

| 问题 | v1.2.0 状态 | v1.2.1 状态 | 对比 |
|------|:----------:|:----------:|:----:|
| **risk duplicate** | 8 阻塞项含重复 | **4 阻塞项无重复** | ✅ fixed |
| **docs suggested tests** | CLAUDE.md 触发测试建议 | CLAUDE.md 不触发 | ✅ fixed |
| **unknown file types** | 3 模块 ❓ unknown | **全部模块有风险等级** | ✅ improved |
| **codex approval pending** | 假阳性阻塞 | **已移除** | ✅ fixed |
| **idle explanation** | 无解释 | **有解释说明** | ✅ improved |

### 详细对比

#### 1. Risk 重复
- 之前: 8 blocking issues (3 对重复 + Codex + Test results)
- 现在: 4 blocking issues (3 唯一 + Test results)
- 修复: merge_readiness.py dedup key 同时覆盖 `priority=` 和 `level=` 格式

#### 2. 文档文件建议
- 之前: "Add tests for CLAUDE.md"、"Add tests for CODEX-CLOUD-HANDOFF.md"
- 现在: 不再对这些文件生成测试覆盖建议
- 修复: suggestion_engine.py 增加 `NON_SOURCE_EXTENSIONS` + 已知文件名列表

#### 3. Unknown 文件类型
- 之前: `openclaw-agents-v2`, `docs`, `examples` 显示 ❓ unknown
- 现在: 全部显示 ✅ 低 或 🟡 中
- 修复: project_scanner.py 增加模块默认风险到 LOW

#### 4. Codex 误报
- 之前: "Codex approval pending" 出现在非 Codex 项目的 blocking issues
- 现在: 普通项目不再显示 Codex gate
- 修复: merge_readiness.py 增加 `has_loop_artifacts` 参数

#### 5. Idle 解释
- 之前: 仅显示 "idle / 0% 置信度"，无解释
- 现在: 新增解释文本
- 修复: agent_state/renderer.py 增加 idle 解释

---

## 结论

**✅ v1.2.1 稳定化成功。** 全部 5 项修复在 CPIS 真实项目上验证通过。
