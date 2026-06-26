
<p align="center">
  <img src="https://img.shields.io/badge/version-v1.4--loop--installer--mvp-blue?style=flat-square" alt="版本">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/copilot_tests-958%20passed-brightgreen?style=flat-square" alt="Copilot 测试">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="许可证">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<h1 align="center">Harness OS</h1>
<p align="center"><em>Agentic Engineering Governance Platform</em></p>

---

**Harness OS 是一个以治理为先的 AI 编码代理生产循环。** 它将 AI 生成的代码从无监督的补丁变成经过规划、审查、证据验证和审计的工程变更。

---

## 快速开始

### 方式 1：Python CLI（推荐）

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
python -m pip install -e .
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
python -m harness.copilot.cli dashboard .
python -m harness.copilot.cli inspect .
```

### 方式 2：Node CLI

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
pnpm install
pnpm build
./dist/index.js version
./dist/index.js doctor
```

---

## 架构

```
Codex（规划器）→ 任务合同 → Worker（执行）→ 结果证据 → 审查 → Codex 最终关卡 → 审计追踪
```

## 核心概念

- **证据层次**：测试结果 > 审计事件 > 审查结果 > 代码差异 > Worker 声称
- **角色分离**：Codex 规划/审查/把关，Hermes 调度/收集证据，Worker 执行
- **修复约束**：最多 3 轮修复，超出则升级
- **高风险操作**：commit/push/merge 需要人类批准

详见 [架构文档](docs/architecture.md)。

---

## 当前状态

- **版本**: v1.4-loop-installer-mvp
- **CLI 命令**: 40+
- **Python 测试**: 958 passed / 1 skipped
- **完成 Loop**: 2 个完整证据链
- **许可证**: ISC
