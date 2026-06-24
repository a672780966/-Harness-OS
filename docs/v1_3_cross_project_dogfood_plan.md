# v1.3 Cross-Project Dogfood Plan

**首个 dogfood 项目**: Competitive-Product-Intelligence-System (CPIS)
**验证结果**: v1.2.1 全部 5 项修复通过
**目标**: 建立可重复的 cross-project 验证流程

---

## 1. 每个项目生成的输出

```
<project>/
└── .harness/
    ├── copilot_demo/
    │   ├── dashboard_<date>.md       # markdown dashboard 快照
    │   ├── readiness_<date>.md       # merge readiness 报告
    │   ├── agent_state_<date>.md     # agent 生命周期状态
    │   ├── pr_comment_<date>.md      # PR comment 文本
    │   ├── pr_pack_<date>/           # PR pack 多文件
    │   ├── static_shell_<date>/      # HTML shell dashboard
    │   └── live_dashboard_<date>/    # Live dashboard HTML
    ├── runtime/
    │   ├── last_action_result.json
    │   └── provider_health.json
    └── dogfood_findings_<date>.md    # 发现报告
```

## 2. 输出目录规范

| 规范 | 规则 |
|------|------|
| 位置 | `<project-root>/.harness/copilot_demo/` |
| 日期 | ISO 日期 `_2026_06_23` 后缀 |
| 文件格式 | `.md` 纯文本, JSON 快照 |
| HTML 位置 | `static_shell_<date>/index.html` |
| 不修改 | 项目源代码 (`src/`, `backend/`, `frontend/` 等) |
| 可 gitignore | `.harness/` 应加入 `.gitignore` |

## 3. 项目源码只读保证

所有 Harness Copilot 命令内建 readonly:
- ✅ 不修改目标项目文件
- ✅ 不创建 `.harness/` 之外的文件
- ✅ 不运行测试
- ✅ 不创建 git commit/tag
- ✅ 不调用外部 API
- ✅ 不保存凭据

## 4. Findings Report 模板

```markdown
# Dogfood Findings: <project-name>

**日期**: <date>
**Harness 版本**: <tag/commit>
**项目路径**: <path>
**分析范围**: <full / diff-only / loop-only>

---

## 1. 项目结构识别准确性
...
## 2. 模块卡片实用性
...
## 3. 风险分类合理性
...
## 4. Merge Readiness 可信度
...
## 5. PR Comment 可用性
...
## 6. Live Dashboard
...
## 7. 输出为空的项
...
## 8. 发现的缺口/误报
...
## 9. 建议修复/改进
...
```

## 5. Regression Fixes 回写流程

```
Dogfood → Findings → Issue → Fix → Test → Commit → New Tag
```

步骤:
1. 对目标项目运行完整 dogfood 流程
2. 生成 findings report
3. 评估误报/缺口:
   - 属于 Harness 缺陷 → 修复 Harness 源码 → 新 test → commit → tag
   - 属于目标项目特性 → 记录到 known limits
   - 属于 v1.3 功能缺口 → 记录到 planning doc
4. 修复后重新运行 dogfood 验证
5. 更新 findings report 对比状态

## 6. 何时允许进入 v1.3 Coding

**进入条件**（满足任意 2 项）:

- [ ] 至少 3 个不同类型的项目经过 dogfood 验证
- [ ] 至少 1 个假阳性被发现并修复
- [ ] 至少 1 个 Windows/WSL2 依赖检查通过
- [ ] Provider reliability 回退方案设计完成
- [ ] Installation 流程文档完成

**否决条件**（满足任意 1 项即阻塞）:

- [ ] 当前 version 有未修复的 P0 缺陷
- [ ] sealed evidence 被修改
- [ ] tests 不合格 (< 750 passed)

## 7. 推荐的下一批 Dogfood 项目

| 项目类型 | 推荐 | 验证重点 |
|---------|------|---------|
| Python 后端 | CPIS (已完成) | 全部功能 |
| TypeScript 前端 | 一个 React/Next.js 项目 | TypeScript 模块识别 |
| Mixed monorepo | 含 Go/Rust/JS 的仓库 | 多语言支持 |
| Documentation-heavy | 主要含 .md 的项目 | 文档过滤正确性 |
| Empty/minimal | 新 clone 空项目 | idle 状态解释 |
