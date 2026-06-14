
<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--rc.2-blue?style=flat-square" alt="版本">
  <img src="https://img.shields.io/badge/TypeScript-6.0-blue?style=flat-square" alt="TypeScript">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="许可证">
  <img src="https://img.shields.io/badge/tests-528%20passed-brightgreen?style=flat-square" alt="测试">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<h1 align="center">Harness OS</h1>
<p align="center"><em>Codex‑first 项目操作系统 — 可治理、可审计、可复现的 Agent 工程平台</em></p>

---

**Harness OS** 是一个面向 AI 编码 Agent 的操作系统。框架赋予 Agent *能力*，而 Harness OS 赋予 Agent *边界和纪律*：每一次工具调用都经过门禁，每一个输出都经过脱敏，每一个决策都被追踪，每一次交付都经过验证。

可以把它理解为 **AI Agent 的 Kubernetes**——不是用来跑容器的，而是用来跑 Agent 化工作流，内置治理、观测和审计能力。

---

## 为什么需要 Harness OS？

像 LangChain、Vercel AI SDK 和 OpenAI Agents SDK 这样的框架让 Agent 能够调用工具、使用模型、组合工作流。但它们无法回答：

- **谁批准了这次工具调用？** → Harness OS 记录每一次调用的会话、轮次和 Agent 身份。
- **输出中泄露了密钥吗？** → Harness OS 在每一个输出边界自动脱敏 15+ 种密钥模式。
- **能回放刚才发生了什么吗？** → 每次运行都被记录为结构化链路，包含事件、审批和检查点。
- **交付安全吗？** → 在 commit、PR 或 deploy 之前，验证必须通过加密完整性哈希检查。
- **能强制策略吗？** → 多层配置体系，包含不可变字段、单向安全收紧规则和 fail‑closed 默认值。

Harness OS **不是一个框架**。它是一个**治理层**，包裹在任何 Agent 运行时之外，让 Agent 达到生产就绪状态。

---

## 架构

```
┌─────────────────────────────────────────────────────┐
│                   CLI (harness)                      │
│  create │ open │ init │ run │ verify │ deliver        │
│  config │ status │ report │ checkpoint │ rollback     │
│  skills │ decision │ repair │ check                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Turn Orchestrator                     │
│  Session → Input → Model Call → Tool Gate → Response │
└──────┬─────────┬──────────┬──────────┬─────────────┘
       │         │          │          │
┌──────▼──┐ ┌───▼────┐ ┌──▼────┐ ┌──▼──────────┐
│ Policy  │ │Approval│ │Secret │ │Observability │
│ Engine  │ │ Gate   │ │Redact │ │ Trace/Events │
└─────────┘ └────────┘ └───────┘ └──────────────┘
       │         │          │          │
┌──────▼─────────▼──────────▼──────────▼──────────┐
│            Verification & Delivery                │
│  Guard → Commit → PR → Release → Deploy          │
└──────────────────────────────────────────────────┘
```

### Thin Harness（已实现）

治理每一个 Agent 动作的最小可行闭环：

1. 接收 Turn 输入
2. 执行模型调用
3. 生成工具提案
4. **PreToolUse 门禁** — 策略评估 + 密钥扫描
5. **Allow / Deny / NeedsApproval** 决策
6. **审批解析**（如果需要）
7. 工具执行
8. **PostToolUse 追踪** — 记录一切
9. 输出脱敏后的最终响应

### Thick Harness（规划中）

面向生产级部署的扩展能力：
- 并行 Hook 扇出（发布‑收集模式）
- OpenTelemetry 集成
- 策略热加载（无需重启）
- 多 Provider 故障切换（Claude ↔ GPT ↔ 其他）
- 基于预算的 Provider 路由
- 分布式审批 UI
- 沙箱化工具执行

---

## 快速开始

### 前置条件

- [Node.js](https://nodejs.org/) >= 22
- [pnpm](https://pnpm.io/) >= 11

### 安装与构建

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd Harness-OS
pnpm install
pnpm build
```

### 运行

```bash
# 显示版本
pnpm harness --version
# → 1.0.0-rc.2

# 显示帮助
pnpm harness --help

# 显示配置
pnpm harness config

# 显示配置（JSON 格式）
pnpm harness config --json

# 列出可用技能
pnpm harness skills list

# 检查 AGENTS.md 有效性
pnpm harness check

# 在项目中初始化 Harness OS
pnpm harness init --json

# 执行任务
pnpm harness run "为认证模块添加测试"
```

### 常见工作流

```bash
# 1. 初始化项目
cd my-project
harness init

# 2. 执行任务
harness run "实现用户身份认证"

# 3. 运行验证
harness verify

# 4. 准备交付
harness deliver --commit --ver-id <验证ID>
```

---

## CLI 命令

| 命令 | 说明 |
|---|---|
| `create <name>` | 创建新的 Harness OS 项目 |
| `open <path>` | 打开已有项目 |
| `init` | 在已有项目中初始化 Harness OS |
| `repair` | 修复缺失或无效的项目结构 |
| `check` | 检查 AGENTS.md 有效性 |
| `status` | 显示当前项目状态 |
| `run <task>` | 执行任务（完整流水线） |
| `resume <run-id>` | 恢复暂停或中断的运行 |
| `verify` | 运行验证流水线（lint、类型检查、测试、构建） |
| `report <run-id>` | 显示运行报告 |
| `deliver` | 准备交付（commit / PR / release / deploy） |
| `decision` | 管理架构决策（ADR） |
| `skills` | 管理和列出技能 |
| `checkpoint` | 创建保存 git 和任务状态的检查点 |
| `rollback <checkpoint-id>` | 显示回滚信息 |
| `config` | 显示 Harness OS 配置 |

所有命令支持 `--json`（机器可读输出）和 `--quiet`（最小化输出）。

---

## 内置能力

### 治理与安全
- **权限三态**：`allow` | `deny` | `needs_approval` — 无模糊状态
- **密钥脱敏**：15+ 种模式类型 — API 密钥、令牌、私钥自动从所有输出中脱敏
- **文件保护**：危险路径被阻止 Agent 访问
- **安全字段**：不可变配置字段、单向弱化保护、联合合并数组
- **Fail‑closed**：任何 Hook 失败默认 `needs_approval`

### 验证
- 从 `AGENTS.md` 和 `package.json` 自动检测项目命令
- 运行完整流水线：lint → 类型检查 → 测试 → 构建
- 生成带加密完整性哈希的结构化 JSON 结果
- 绑定到项目、任务、运行和 git commit，实现不可抵赖

### 交付流水线
- 守卫检查：验证绑定、git 状态、项目完整性
- 规约式 commit 消息生成
- PR 正文生成
- 带完整审计线索的交付报告

### 观测
- **事件**：带会话、参与者和脱敏的 JSONL 事件日志
- **链路**：完整的工具调用、上下文包、检查点运行跟踪
- **报告**：带验证结果的 Markdown 运行报告

### 技能注册表
内置技能，按风险分级和审批要求分类：

| 技能 | 风险 | 工具 |
|---|---|---|
| Filesystem | 中 | 读、写、列表、搜索、删除 |
| Shell | 高 | 运行命令、测试、构建 |
| Git | 中 | 状态、差异、提交、推送 |
| Repo Scanner | 低 | 扫描、检测、映射 |

---

## 项目结构

```
Harness-OS/
├── src/
│   ├── cli/              # CLI 入口 + 格式化器
│   ├── config/           # 分层配置加载器（安全感知）
│   ├── governance/       # 策略引擎、脱敏器、Hook 框架
│   ├── project/          # 项目生命周期（create/open/init/repair）
│   ├── task/             # 任务生命周期（create/complete/fail）
│   ├── decision/         # ADR 管理（propose/accept/reject）
│   ├── verification/     # 验证流水线 + 结果绑定
│   ├── delivery/         # 交付流水线（guard/commit/PR/report）
│   ├── observability/    # 事件、链路、运行报告
│   ├── runtime/          # 会话、流水线、轮次编排
│   ├── context/          # Context Pack 构建
│   ├── skills/           # MCP 技能注册表
│   └── state/            # 运行、检查点、SQLite 状态
├── tests/
│   ├── unit/             # 528 个单元测试
│   └── integration/      # 28 个集成测试
├── harness_os_docs/      # 完整设计规范（12 份文档）
├── .claude/              # Claude Code 项目配置
└── .project/             # Harness OS 本地状态（已 gitignore）
```

---

## 文档

完整的设计和工程规范位于 [`harness_os_docs/`](harness_os_docs/README.md)：

| 文档 | 说明 |
|---|---|
| [01_ARCHITECTURE](harness_os_docs/01_ARCHITECTURE.md) | 系统架构和核心原则 |
| [02_CODEX_DEVELOPMENT_SPEC](harness_os_docs/02_CODEX_DEVELOPMENT_SPEC.md) | Codex 开发规范 |
| [03_AGENTS_MD_STANDARD](harness_os_docs/03_AGENTS_MD_STANDARD.md) | AGENTS.md 协议标准 |
| [04_HARNESS_OS_DESIGN](harness_os_docs/04_HARNESS_OS_DESIGN.md) | 详细系统设计 |
| [05_CONTEXT_ENGINEERING](harness_os_docs/05_CONTEXT_ENGINEERING.md) | 上下文工程规范 |
| [06_TASK_DECISION_PROJECT_MANAGER](harness_os_docs/06_TASK_DECISION_PROJECT_MANAGER.md) | 任务、决策和项目管理 |
| [07_MCP_SKILLS_SPEC](harness_os_docs/07_MCP_SKILLS_SPEC.md) | MCP 技能规范 |
| [08_GOVERNANCE_SECURITY](harness_os_docs/08_GOVERNANCE_SECURITY.md) | 治理与安全规则 |
| [09_VERIFICATION_OBSERVABILITY](harness_os_docs/09_VERIFICATION_OBSERVABILITY.md) | 验证与可观测性 |
| [10_DELIVERY_PIPELINE](harness_os_docs/10_DELIVERY_PIPELINE.md) | 交付流水线规范 |
| [11_ACCEPTANCE_CRITERIA](harness_os_docs/11_ACCEPTANCE_CRITERIA.md) | 最终验收标准 |
| [12_OPEN_SOURCE_REFERENCES](harness_os_docs/12_OPEN_SOURCE_REFERENCES.md) | 开源参考映射 |
| [13_TESTING_STRATEGY](harness_os_docs/13_TESTING_STRATEGY.md) | 测试策略 |
| [14_ERROR_CODES](harness_os_docs/14_ERROR_CODES.md) | 错误码参考 |
| [15_CONFIG_REFERENCE](harness_os_docs/15_CONFIG_REFERENCE.md) | 配置参考 |
| [16_CLI_OUTPUT_CONTRACT](harness_os_docs/16_CLI_OUTPUT_CONTRACT.md) | CLI 输出合约 |
| [17_PROJECT_STORAGE_GIT_POLICY](harness_os_docs/17_PROJECT_STORAGE_GIT_POLICY.md) | Git 和存储策略 |
| [18_MIGRATION_VERSIONING](harness_os_docs/18_MIGRATION_VERSIONING.md) | 迁移与版本管理 |

---

## 开发

```bash
# 类型检查
pnpm typecheck

# 运行单元测试
pnpm test:unit

# 运行集成测试
pnpm test:integration

# 运行全部测试
pnpm test

# 运行带覆盖率测试
pnpm test:coverage

# 构建
pnpm build

# 格式化代码
pnpm format
```

### 测试状态

- **528 个单元测试** — 19 个测试文件，全部通过
- **28 个集成测试** — 1 个测试文件，全部通过
- **覆盖率阈值**：80%（在 vitest.config.ts 中配置）
- **TypeScript**：严格模式，`src/` 中已彻底消除 `as any`

---

## 设计原则

1. **边界清晰**：每个模块职责明确，没有上帝对象。
2. **权限保守**：默认 `needs_approval`，从不默认 `allow`。
3. **状态可追踪**：每次写入都有 schema、作用域、参与者、原因和跟踪 ID。
4. **工具可审计**：每次调用记录谁、什么、输入、决策和时间戳。
5. **低耦合**：先有 Thin Harness，Thick Harness 作为扩展，绝不混入。
6. **Fail‑closed**：任何 Hook 失败、超时或不可解析结果 → `needs_approval`。

---

## 状态

**v1.0.0-rc.2** — 核心治理和验证的发布候选版本。

已实现：
- ✅ CLI 框架（17 个命令）
- ✅ 多层配置 + 安全字段强制
- ✅ 密钥脱敏（15+ 模式，覆盖所有输出边界）
- ✅ 带完整性绑定的验证流水线
- ✅ 带守卫检查的交付流水线
- ✅ 可观测性（事件、链路、运行报告）
- ✅ ADR 管理（提案/接受/拒绝/取代）
- ✅ 会话和状态管理
- ✅ 任务生命周期（创建 → 运行 → 完成 → 报告）
- ✅ 技能注册表（4 个内置技能）
- ✅ 检查点和回滚分析
- ✅ 528 个单元测试 + 28 个集成测试

v1.1+ 规划：
- 策略热加载
- 多 Provider 运行时（Claude + GPT + 开源模型）
- 分布式审批 UI
- OpenTelemetry 导出
- 沙箱化工具执行

---

## 许可证

ISC
