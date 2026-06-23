# v1.3 Planning: Cross-Project Dogfood + Windows/WSL2 Runtime

**基线**: v1.2.1-dogfood-stabilized (commit 045e29a)
**日期**: 2026-06-23
**状态**: plan (not implementing)

---

## 规划目标

v1.3 不是功能冲刺，而是**可迁移性冲刺**。目标是把 v1.2.1 从"在 Harness OS 仓库里能用"变成"在任何项目、任何机器上都能用"。

## 五大规划主题

| # | 主题 | 核心问题 |
|---|------|---------|
| 1 | **Windows/WSL2 Runtime** | 如何在 Windows 机器上跑 Harness Copilot？ |
| 2 | **Cross-Project Dogfood** | 如何持续用真实项目验证 Copilot 质量？ |
| 3 | **Provider Reliability** | degraded 状态如何解决或绕过？ |
| 4 | **Installation / Packaging** | 如何让新用户 5 分钟内跑起来？ |
| 5 | **Multi-Project Workspace** | 如何管理多个 analysed 项目？ |

## 决策树

```
v1.3 scope decision tree:

1. 平台支持
   ├─ Windows native (高风险, 延后)
   └─ Windows WSL2 (推荐走)

2. 项目支持
   ├─ 单个项目扫描 (已有)
   └─ 多项目 workspace (v1.3 开始)

3. 远程 API
   ├─ GitHub/GitLab API (延后)
   └─ 本地 file-based (v1.3 不动)

4. Provider
   ├─ 等上游修复 (被动)
   └─ fallback 模型 (主动, 建议入 v1.3)
```

## 推荐 v1.3 范围

**包括**:
- ✅ Windows/WSL2 Runtime 支持 + 安装文档
- ✅ Cross-project workspace + Dogfood 工作流
- ✅ Provider fallback / 多 provider 配置
- ✅ Installation / bootstrap 脚本 + pip/pipx 包

**延后**:
- ⏳ GitHub/GitLab API 集成
- ⏳ 自动 Agent 编排
- ⏳ 自动代码修复
- ⏳ Cloud Sync / DB 持久化
- ⏳ 3D StarMap UI
- ⏳ Windows native (非 WSL2)
