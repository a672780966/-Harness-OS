# v1.3 Scope Decision

**基线**: v1.2.1-dogfood-stabilized
**决策依据**: CPIS dogfood 验证 + 当前 provider 状态 + 可迁移性需求

---

## 推荐 v1.3 范围

### ✅ 包括

| # | 项目 | 理由 | 工作量估计 |
|---|------|------|:---------:|
| 1 | **Windows WSL2 Runtime 文档** | 最大用户群在 Windows | 小 (纯文档) |
| 2 | **Cross-project workspace** | 支持 `--project <path>` 切换 | 中 (CLI + schema) |
| 3 | **~/.harness/config.yaml 全局配置** | 统一 provider、timeout 管理 | 中 (config loader) |
| 4 | **Provider fallback 链** | 解决 degraded 阻塞问题 | 中 (provider_guard 扩展) |
| 5 | **Installation / pipx 包** | 新用户 5 分钟可跑 | 小 (pyproject.toml + 文档) |

### ⏳ 延后到 v1.4+

| # | 项目 | 理由 |
|---|------|------|
| 1 | GitHub/GitLab API 集成 | 需要 access token、webhook、权限管理 |
| 2 | 自动 Agent 编排 | 需要在解决 provider reliability 后 |
| 3 | 自动代码修复 | 依赖 GitHub API 和 Agent 编排 |
| 4 | Cloud Sync / 远程 DB | 需要认证、加密、多用户 |
| 5 | 3D StarMap UI | 纯展示，无功能价值 |
| 6 | Windows native | 路径/编码/脚本问题太多 |

### ❌ 不纳入 v1.3

| 项目 | 理由 |
|------|------|
| 音乐 / 音频生成 | 与项目无关 |
| Enterprise RBAC | 超出 MVP 范围 |
| LLM-based 分析引擎替换 | 当前 rule-based 够用 |
| Evaluation runner 集成 | 属于另一条产品线 |

---

## 决策树

```
v1.3 scope ─┬─ Must include ───┬─ Windows WSL2 doc (cheap, high impact)
             │                   ├─ ~/.harness/config.yaml (unblocks provider)
             │                   ├─ Provider fallback chain (fixes degraded)
             │                   ├─ Cross-project workspace (enables scaling)
             │                   └─ pipx installation (enables distribution)
             │
             ├─ Can defer ──────┬─ GitHub API (high effort, unclear need)
             │                   ├─ Auto agent (blocked by provider)
             │                   ├─ Cloud sync (over-engineering)
             │                   └─ 3D UI (cosmetic)
             │
             └─ Out of scope ───┬─ Music API
                                 ├─ RBAC
                                 ├─ LLM engine replacement
                                 └─ Evaluation runner
```

## 实施顺序建议

```
Phase 1: Foundation (无功能变更)
  ├─ ~/.harness/config.yaml loader
  ├─ 全局 provider 配置
  └─ pipx packaging

Phase 2: Runtime
  ├─ Windows WSL2 安装文档
  ├─ 跨平台依赖检查脚本
  └─ WSL2 验证清单

Phase 3: Scaling
  ├─ Cross-project workspace (--project 参数)
  ├─ 多项目 dogfood 工作流
  └─ Findings 自动化模板

Phase 4: Reliability
  ├─ Provider fallback chain
  ├─ 多 provider auto-detect
  └─ canary 结果记录优化
```

## Blockers for v1.3 Start

| Blocker | 解决 | 状态 |
|---------|------|:----:|
| Provider degraded | v1.3 Phase 1 解决 | ⏳ pending |
| Windows/WSL2 未封测 | v1.3 Phase 2 验证 | ⏳ pending |
| pipx 包未发布 | v1.3 Phase 1 制作 | ⏳ pending |

**结论**: 无硬阻塞。v1.3 可以从 Phase 1 开始（Foundation 阶段不依赖 provider）。
