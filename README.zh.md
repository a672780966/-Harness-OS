
<p align="center">
  <img src="https://img.shields.io/badge/version-v1.4--loop--installer--mvp-blue?style=flat-square" alt="版本">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/copilot_tests-616%20passed-brightgreen?style=flat-square" alt="Copilot 测试">
  <img src="https://img.shields.io/badge/full_pytest-848%20passed-brightgreen?style=flat-square" alt="全量测试">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="许可证">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<p align="center">
  <img src="assets/brand/mobius-system-identity-v1.png" width="128" height="128" alt="Mobius 系统身份标识">
</p>

<h1 align="center">Mobius</h1>
<p align="center"><em>面向 AI 生产过程的时间治理系统</em></p>

---

**Mobius 是一种面向生成式系统的时间治理结构。**

它以终局约束行动，
以证据建立信任，
以记忆保存后果，
以边界生成能力，
以演化修正未来判断。

它不让 Agent 永恒存在。
它让每一次短暂执行都有机会回到系统，成为证据、记忆、边界、能力或一次明确的裁决。

<p align="center">
  <a href="#快速开始"><strong>▶ 5 分钟快速上手</strong></a>
</p>

---

## Mobius 为什么存在

现代 AI Agent 在执行推理、编码、工具调用和多 Agent 协作方面越来越强。但能力本身并不会让 AI 生产过程变得可信。

更困难的问题是治理：

- 目标从哪来？
- 谁有执行权？
- 谁授予工具权限？
- 谁来评估结果？
- 谁来决定继续、停止、重试、回滚还是交给人？

当前的 Agent 框架回答"如何执行"。Mobius 回答"如何在时间维度上治理执行"。

**Mobius 存在，是因为 AI 生产需要的不只是更强的 Agent，而是让 Agent 生产过程可治理、可验证、可沉积、可演化的时间型控制系统。**

---

## 快速开始

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
# 方式 1：Python CLI（无需安装）
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
python -m harness.copilot.cli inspect .
python -m harness.copilot.cli dashboard .
python -m harness.copilot.cli pr-draft --base main

# 方式 2：Node CLI（需要 pnpm + node）
pnpm install
pnpm build
./dist/index.js version --json
./dist/index.js doctor
```

如果 `harness` 命令不可用：
```bash
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
```
构建后（`pnpm install && pnpm build`），`harness` bin 位于 `./dist/index.js`。

---

## 核心哲学

### 终局先于行动 (Purpose Before Action)

一切执行都必须服务于明确的终局。任何 Agent 在行动前，都必须知道：为什么开始、要去哪里、什么叫完成、什么不能背叛。没有终局，行动只是漂流；没有终局，Loop 只是空转。

*Future Layer 的意义不只是保存需求，而是保存终局、方向、验收标准和不可违反的不变量。*

### 行动必须归还 (Every Action Must Return)

每一次执行都会产生后果。后果不能跟随临时 Agent 一起消失。它们必须归还为证据、轨迹、风险、成本、失败、边界或能力。如果系统接住了后果，它转化为秩序；如果接不住，它以噪声、漂移、债务或风险的形式返回。

*Mobius 遵循执行守恒律：没有一次执行会真正消失。每一次行动都被转化为秩序，或者以混乱的形式返回。*

### 证据先于信任 (Evidence Before Trust)

AI 不能自证完成。Agent 的声明不是完成。模型的总结不是事实。可信来自 trace、diff、test、review、audit，以及——在高风险或最终授权场景中——人工批准。没有证据的完成，不进入可信状态。没有审计的结果，不进入系统记忆。没有验证的经验，不进入未来判断。

*Mobius 不信任"看起来完成"。Mobius 只接受"被证明完成"。*

### 能力来自边界 (Capability Emerges from Boundaries)

真正的能力不是"什么都能做"，而是知道什么时候做、做到哪里停、什么需要证据、什么必须交给人、什么不能再重复。成功提供路径。失败提供边界。证据确认路径。记忆保存边界。系统从二者之间生成能力。

*Mobius 不把失败简单记录为错误。它要求失败最终转化为边界——规则、权限调整、风险标记或新的能力约束。*

### 系统必须演化 (The System Must Evolve)

Agent 可以是临时的。Worker 可以被销毁。一次任务可以结束。但系统不能原地踏步。每次行动后，Mobius 必须判断：是否应该沉积为记忆？是否应该生成能力？是否应该更新边界？是否应该调整权限？是否应该把判断权交还给人？是否应该明确丢弃这次经验？

*演化不等于永远新增。有时演化是记住。有时演化是遗忘。有时演化是降低置信度。有时演化是阻断路径。有时演化是把判断权交还给人。*

---

## 架构

Mobius 将 AI 生产过程拆分为四个时间治理层。

### 未来层（目标约束）

未来不是预测。未来是约束。Future Layer 保存终局、目标、验收标准、项目方向和不可违反的不变量。它回答：为什么开始？要去哪里？什么叫完成？什么不能背叛？它不负责执行，它负责防止执行漂流。

*未来层 = 章程 / 规格 / 验收标准 / 项目方向*

### 现在层（临时执行）

现在不是自由行动。现在是临时 Agent 在有限权限内完成一次可验证执行。现在层负责任务执行、工具调用、代码修改、测试运行、局部修复和证据生成。但它不能长期持有全局记忆，不能绕过 Tool Gateway，不能自行宣布可信完成，不能伪造最终授权。

*现在层 = Worker / 工具执行 / 证据生成*

### 过去层（经验沉积）

过去不是聊天记录。过去是经过证据验证的系统记忆。过去层保存执行轨迹、失败原因、修复路径、测试结果、审计事件、决策记录、能力路径和风险边界。只有带有来源、置信度、有效期、验证状态和审计记录的经验，才有资格进入过去层。

*Mobius 不记住一切。Mobius 只沉积能够影响未来判断的事实。*

*过去层 = StarMap / Audit Log / 已验证路径 / 失败记忆*

### 演化层（系统演化）

演化层是唯一不参与具体执行、却判断整个系统是否变好的治理视角。它不看一次任务是否完成，而是看：系统是否更接近终局？是否产生了新的能力？是否暴露了新的边界？是否降低了未来风险？是否需要调整未来层？是否需要交还给人？

*演化层 = 元评估 / 治理审计 / 沉积决策*

*这是 Mobius 与普通 Agent 框架的关键区别：它不是解释 Agent 如何运行，而是解释一个生成式系统为什么能够持续演化。*

---

## Harness OS：参考实现

Harness OS 是 Mobius Architecture 的第一个且目前唯一的参考实现。

它将运行时层——Captain、Worker、Audit、StarMap、Loop Controller、Tool Gateway——实现为一个具体的工程产品，通过代码执行 Mobius 原则。

- **理论上可替换**：Mobius Architecture 不依赖特定运行时，可以有其他实现。
- **实践中唯一**：Harness OS 是第一个且目前唯一的参考实现，没有第二个运行时。

Harness OS **不是**模型提供商，不是通用编码框架，也不是云 SaaS 产品。它是一个面向 AI 辅助工程的本地优先治理运行时。

---

## 当前状态

- **主线基线**: `v1.4-loop-installer-mvp`
- **最新能力**: `v1.4-loop-installer-mvp`
- **Copilot 测试**: `616 passed`
- **全量测试**: `848 passed`
- **产品模式**: Local Semantic Copilot MVP
- **Tag 策略**: 仅推送公开安全 tag，大证据包不进入 Git tag

### v1.1 — Real Hermes Loop
- 图规划器、循环运行/控制器、执行/审计
- 评估触发修复、审查触发修复、最终关卡、证据包

### v1.2 — Local Semantic Copilot MVP
- 项目检查、差异摘要、任务卡、合并就绪度
- 证据包、静态仪表盘、实时监控、Agent 状态机
- PR/MR 包、提供商可靠性守卫、实时仪表盘

### v1.2.1 — Dogfood 稳定性
- 风险去重、源文件/文档过滤、文件类型扩展
- 误报修复、空克隆空闲解释

### v1.3 — 运行时基础
- 配置 schema / loader / resolver / validator
- 运行时诊断、版本命令、提供商可靠性规划
- 跨项目运行时规划、公开安全证据策略

### v1.3.1 — PR 草稿助手
- `harness copilot pr-draft`、GitHub CLI 检测
- 手动备用 PR 草稿生成、大文件/缓存拦截检查
- 可选认证 `--create`

---

## Tag / Evidence 策略

部分本地 sealed tag 未推送到 GitHub，因为其可达历史包含 373 MB SWE-bench 证据包，超出 GitHub 100 MB blob 大小限制。

仅推送公开安全的 tag。大证据包应通过 Release Asset 或外部冷存储发布，Git 仅保留清单和 SHA256 引用。

---

## 重要文档

- [v1.3 Main Integration Seal](docs/v1_3_main_integration_seal.md)
- [v1.2 Alpha Final Seal Manifest](docs/v1_2_alpha_final_seal_manifest.md)
- [v1.2 Alpha Command Reference](docs/v1_2_alpha_command_reference.md)
- [Public-Safe Evidence Strategy](docs/public_safe_evidence_strategy.md)
- [Public-Safe Tag Mapping](docs/public_safe_tag_mapping.md)
- [Large Evidence Archive Manifest](docs/large_evidence_archive_manifest.md)
