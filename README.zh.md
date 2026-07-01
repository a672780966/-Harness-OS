# Captain Code

> 可审计的 AI 编码工作流。

![License](https://img.shields.io/badge/license-ISC-green?style=flat-square)
![Status](https://img.shields.io/badge/status-early%20development-orange?style=flat-square)
![Mode](https://img.shields.io/badge/mode-local--first-blue?style=flat-square)

[English](./README.md) · **中文** · [日本語](./README.ja.md) · [한국어](./README.ko.md)

---

## Captain Code 是什么

Captain Code 是一个可审计的 AI 编码工作流，它把开发任务转化为**受控执行、可审查的证据、门禁决策与归还记录**。

它帮助开发者使用 AI 编码 agent，而不必盲目信任 agent 的原始输出。Captain Code 不接受“agent 说完成了”这种说法，而是要求每个任务都带有契约、每次执行都留下证据，并且在门禁决策接受之前，任何结果都不会进入可信状态。

Captain Code 是**本地优先（local-first）**、读优先的。它在你本机、针对你的仓库运行，绝不会自行 push、发布或部署。

## 要解决的问题

AI 编码 agent 擅长生成 diff 和自信的总结，却不擅长证明这些改动是正确的、在范围内的、可以安全接受的。

- agent 的声明不是证据。
- 通过的总结不等于通过的测试。
- 看起来“已完成”的 diff，并不等于可以安全合并的 diff。

如果 agent 周围没有工作流，你最终会信任未经验证的输出。Captain Code 在 agent 与你的可信状态之间加入一层薄薄的、可审计的环节，让“接受”成为有证据支撑的决策，而不是凭感觉。

## 核心工作流

```
TaskEnvelope → Invocation → Artifact / Evidence → Review → GateDecision → AuditEvent → ReturnRecord
```

| 对象           | 含义                                                       |
| -------------- | --------------------------------------------------------- |
| `TaskEnvelope` | 任务契约：目标、范围、验收标准、约束。                     |
| `Invocation`   | 针对受控工作区的一次执行尝试。                             |
| `Artifact`     | 产出物（diff、生成的文件、补丁、计划）。                   |
| `Evidence`     | 支撑判断的依据（测试结果、日志、策略检查）。               |
| `Review`       | 对 artifact 与 evidence 的评估：通过、修复或阻断。         |
| `GateDecision` | 流程决策：`PASS` / `REPAIR` / `BLOCK` / `ESCALATE`。       |
| `AuditEvent`   | 仅追加（append-only）的发生记录，用于可追溯性。            |
| `ReturnRecord` | 状态归还记录：哪些被接受、被拒绝或仍未解决。               |

这些是**通用协议对象**。Captain Code 是该协议的编码 profile，但这些对象保持可复用，不会被收窄为仅限代码的术语。

## 最小示例

一个任务以 envelope 开始：

```yaml
# task_envelope.yaml
task_id: task-001
title: "Add a usage section to README"
user_request: "Document how to run the CLI in README.md"
scope:
  allowed_paths: ["README.md"]
  denied_commands: ["git push", "git merge"]
acceptance_criteria:
  - "README has a 'Usage' section"
test_commands: ["pnpm test"]
```

随后工作流运行：

1. **Invocation** —— worker 在受控工作区（一个 git worktree）中执行，而不是在你的主工作区。
2. **Artifact / Evidence** —— diff 被记录为 artifact；日志和测试结果被记录为 evidence。
3. **Review** —— 对照验收标准评估 artifact 与 evidence。
4. **GateDecision** —— `PASS`、`REPAIR`、`BLOCK` 或 `ESCALATE`。
5. **AuditEvent** —— 每一步都追加到审计日志。
6. **ReturnRecord** —— 关于哪些被接受、还有哪些风险的最终记录。

在 `GateDecision` 接受并写入 `ReturnRecord` 之前，任何东西都不算“完成”。

## 当前状态

Captain Code 处于**早期、活跃的开发阶段**，请据此看待。

- **模式：** 本地优先、读优先的语义副驾驶（semantic copilot）。
- **当前可用：** 项目巡检、diff 与证据收集、一个 runner 循环（plan → execute → collect → review → gate），以及报告生成。
- **正在加固：** 完整的写入侧 `TaskEnvelope → ReturnRecord` 闭环，包含受控工作区执行与收尾。
- **并非沙箱声明：** 受控工作区是一个 git worktree。它隔离的是*改动*，而不是宿主机。它**不是**安全沙箱（见安全模型）。

> 命名说明：当前 CLI 通过 `harness` / `python -m harness.copilot.cli` 调用，`captain-code` 命名正在逐步采用。参见 [docs/quickstart.md](./docs/quickstart.md)。

## 安全模型

Captain Code 默认保守。以下规则作为工作流的一部分被强制执行，而不是交由 agent 自行决定：

1. **没有 `TaskEnvelope`，就不执行 worker。**
2. **没有 `trace_id`，就没有可信执行。**
3. **没有 diff 引用，就没有完成状态。**
4. **没有测试结果，就没有完成状态。**
5. **失败的测试不能变成已接受。**
6. **超出范围的文件改动会被隔离（quarantine）**，不会被静默应用。
7. **核心协议变更需要人工批准。**
8. **连续三次失败会触发暂停或人工审查。**
9. **`git push`、发布和部署被阻断。**
10. **在 `ReturnRecord` 被信任之前，必须先有被接受的 `GateDecision`。**

受控工作区可以防止污染你的主工作区，并让改动易于 diff 和销毁。但它**无法**阻止恶意命令读取本地文件、环境变量或凭证。强隔离（容器、microVM）不在本阶段范围内。

## Captain Code 不做什么

- 它**不是**“Agent OS”或 AI 操作系统。
- 它**不是**企业治理平台。
- 它**不**替代你的 AI 编码 agent —— 它治理的是 agent 输出如何被接受。
- 它**不**托管登录态，也不内置任何 API Key。
- 它**不**执行 push、发布或部署。
- 它**不**声称自己的工作区是安全沙箱。

## 快速开始

安装与首次运行见 **[docs/quickstart.md](./docs/quickstart.md)**。

随着写入侧闭环的加固，完整的引导式快速开始仍在完善中。只读巡检命令现在即可使用，并且可以安全地在任意仓库上运行。

## 文档

- [Quickstart](./docs/quickstart.md) —— 安装与首次运行
- [Workflow](./docs/workflow.md) —— 协议对象与执行闭环
- [Architecture (lite)](./docs/architecture-lite.md) —— 组件与边界
- [Hermes loop lock](./docs/hermes-loop-lock.md) —— Hermes（State Machine Runner + Scheduler + Daily Reporter）的 runner 规则与安全锁

## 许可证

ISC。
