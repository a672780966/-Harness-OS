# Dogfood Project 001: 竞品公开信息自动采集与分析系统 (CPIS)

## Findings Report

**测试日期**: 2026-06-23
**Harness OS**: `v1.2-alpha-final-sealed` (commit `e733805`)
**目标项目**: Competitive-Product-Intelligence-System
**目标路径**: `~/dogfood/Competitive-Product-Intelligence-System`

---

## 1. 项目结构识别准确性

**✅ 准确 (8/8 模块)**

| 模块 | Harness 识别 | 实际 |
|------|-------------|------|
| `backend` | 🟡 中风险, 82 文件 | ✅ Python FastAPI 核心 |
| `frontend` | 🟡 中风险, 22 文件 | ✅ React 19 + TypeScript |
| `scripts` | 🟡 中风险, 4 文件 | ✅ Shell 脚本 |
| `openclaw-plugins` | ✅ 低风险, 4 文件 | ✅ JS 插件 |
| `openclaw-agents-v2` | ❓ unknown, 6 文件 | ✅ 但无识别类型 |
| `examples` | ❓ unknown, 5 文件 | ✅ 示例数据 |
| `docs` | ❓ unknown, 1 文件 | ✅ 文档 |
| `root` | ✅ 低风险, 4 文件 | ✅ README/CLAUDE/配置 |

**缺口**: `openclaw-agents-v2`、`docs`、`examples` 标记为 `unknown` 风险。这是因为这些模块的文件类型不在 Harness 的已知类型列表中，虽然不影响功能但显示为弱项。

---

## 2. 模块卡片实用性

**🟡 部分有用**

- 文件数和风险等级展示清晰 ✅
- 高风险文件具体路径展示准确 ✅
- 但 `unknown` 模块不提供任何信息，用户无从判断
- 缺少项目技术栈（FastAPI, React, PostgreSQL, Docker）的语义标签

---

## 3. 风险分类合理性

**🟡 大致合理但存在假阳性**

✅ **正确识别**:
- `scripts/verify-deploy.sh` → "包含 security/infra 关键词: deploy" — 确实有部署脚本
- `openclaw-plugins` → 新增大量代码 (+362/-6) — 合理
- `backend` → 中风险 (数据库模型、生产代码变更) — 合理

❌ **假阳性**:
- 建议 "Add tests for CLAUDE.md / CODEX-CLOUD-HANDOFF.md / README.md" — 这些是文档文件，不是需要单元测试的源码。建议引擎将文档文件当成了 "untested source"
- 阻塞项列表出现了 **8 个阻塞项但实际只有 4 个唯一问题** — `openclaw-plugins` 和 `scripts` 各重复了一次 (一次 `priority=`, 一次 `level=`)

---

## 4. Merge Readiness 可信度

**🟡 可信但噪声大**

- 状态 "禁止合并" 是合理的（新 clone 未经 review）✅
- 8 个阻塞项中 3 个是重复的（同一问题以不同 key 输出）❌
- "Codex approval pending" — 这个项目不参与 Codex 流程，是误报
- "Test results not yet available" — 合理，但这是新 clone，没跑过测试 ✅

---

## 5. PR Comment 可直接使用程度

**🟡 可作为起点**

- 结构完整：变更摘要、Agent 状态、合并就绪度、风险清单 ✅
- PR pack 输出 9 个文件，覆盖全面 ✅
- 但重复的阻塞项需要在发布前去重
- 缺少代码级 diff 链接（因为无 GitHub API）
- 建议引擎建议对文档文件加测试，这部分需要手动过滤

---

## 6. Live Dashboard 可打开

**✅ 是**

`file:///home/ctyun/-Harness-OS/.harness/dogfood/competitive_product_intelligence/live_dashboard/index.html`

包含:
- Agent 状态卡 (待命 / idle)
- Merge Readiness 卡 (禁止合并 🔴)
- Risk Level 卡
- Blocking Status 卡
- 建议操作框
- Live Event Timeline ⚠️ 无事件（静态输出）

---

## 7. 输出为空或弱的项

| 输出 | 问题 |
|------|------|
| `Agent State` | 新 clone 无 git 事件，显示 "idle / 0% 置信度" — 这是预期行为，但无解释 |
| `Live Event Timeline` | 静态 HTML 中无事件，但页面正确渲染 |
| `Unknown 风险模块` | `openclaw-agents-v2`, `docs`, `examples` 显示 ❓ unknown，无法提供信息 |
| `Merge Readiness` | 重复的阻塞项降低了可信度 |

---

## 8. v1.2-alpha 对真实项目的缺口

### 实质性缺口

1. **🔴 重复阻塞项** — `generate_risk_alerts()` 返回的 alert 同时包含 `priority=` 和 `level=` 字段，导致 `from_risk_alerts()` 在同一差异上创建两条记录
2. **🟡 建议引擎对文档文件建议加测试** — `generate_suggestions()` 将 `CLAUDE.md` / `CODEX-CLOUD-HANDOFF.md` 识别为 "untested source file"，这些是文档而非源码
3. **🟡 缺少技术栈识别** — 项目使用 FastAPI + React + PostgreSQL + Docker，但 dashboard 只展示文件数/模块名，没有语言/框架标签

### 期望但未实现

4. **❌ Python 专用测试分析** — 项目有 `backend/tests/` 目录（pytest），但 Harness 不做测试运行
5. **❌ frontend package.json 变更检测** — `package.json` 被标记为 "新增依赖"，但未区分 production/dev 依赖
6. **❌ Docker compose 分析** — `docker-compose.yml` 未被任何模块捕获
7. **❌ No GitHub API 集成** — PR comment 无法关联到远程 PR，pr-pack 是本地文件

---

## 9. 是否建议进入 v1.3

**✅ 建议进入 v1.3，但应先修复 v1.2-alpha 的 3 个阻塞问题：**

### 修复优先

1. **风险分类器去重** — `risk_classifier.py` 中 `generate_risk_alerts()` 输出同时包含 `priority=` 和 `level=` 两个键，导致 `from_risk_alerts()` 创建重复卡片
2. **建议引擎过滤非源码文件** — 建议引擎应跳过 `.md`、`.json`、`.yaml` 等非可测试文件
3. **已知类型列表扩展** — `project_scanner.py` 应增加 `.tsx`、`.ts`、`.sh`、`.yml` 等常见文件类型的识别

### v1.3 方向建议

| 方向 | 价值 |
|------|------|
| 远程 API 集成 (GitHub/GitLab) | 高 — PR comment 可发布、issue 可创建 |
| 测试运行集成 | 高 — pytest 结果可纳入 merge 就绪度 |
| 技术栈标识 | 中 — 让 dashboard 更有项目上下文 |
| 多项目/workspace 支持 | 中 — 大型组织同时分析多个仓库 |
| 自定义风险规则 | 低 — 复杂，建议先做去重 |
