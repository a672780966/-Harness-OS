
<p align="center">
  <img src="https://img.shields.io/badge/version-v1.3--main--integration-blue?style=flat-square" alt="版本">
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

<h1 align="center">Harness OS</h1>
<p align="center"><em>本地语义副驾驶 + 可治理的 Agent 工程运行底座</em></p>

---

**Harness OS 是一个本地语义副驾驶与可治理的 Agent 工程运行底座，适用于 AI 辅助软件交付。**

它帮助工程工作流回答：
- 项目现在是什么状态？
- 这次改动影响哪些模块？
- 是否可以合并？
- 审查者应该注意什么风险？
- 哪些证据支持这个判断？
- PR 应该怎么写？

---

## 当前状态

- **主线基线**: `v1.3-main-integration`
- **最新能力**: `v1.3.1-pr-draft-assistant`
- **Copilot 测试**: `616 passed`
- **全量测试**: `848 passed`
- **产品状态**: Local Semantic Copilot MVP
- **Tag 策略**: 仅推送公开安全 tag，大证据包不进入 Git tag

---

## 包含的能力

### v1.1 — Real Hermes Loop
- 图规划器
- 循环运行/控制器
- 执行/审计
- 评估触发修复
- 审查触发修复
- 最终关卡
- 证据包

### v1.2 — Local Semantic Copilot MVP
- 项目检查
- 差异摘要
- 任务卡
- 合并就绪度
- 证据包
- 静态仪表盘
- 实时监控
- Agent 状态机
- PR/MR 包
- 提供商可靠性守卫
- 实时仪表盘

### v1.2.1 — Dogfood 稳定性
- 风险去重
- 源文件/文档过滤
- 文件类型扩展
- 误报修复
- 空克隆空闲解释

### v1.3 — 运行时基础
- 配置 schema / loader / resolver / validator
- 运行时诊断
- 版本命令
- 提供商可靠性规划
- 跨项目运行时规划
- 公开安全证据策略

### v1.3.1 — PR 草稿助手
- `harness copilot pr-draft`
- GitHub CLI 检测
- 手动备用 PR 草稿生成
- 大文件/缓存文件拦截检查
- 可选认证 `--create`

---

## 快速开始

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
python -m pip install --upgrade pip
python -m pip install -e .
harness copilot version --json
harness copilot doctor
harness copilot inspect .
harness copilot readiness .
harness copilot task-card .
harness copilot pr-draft --base main
```

如果 `harness` 命令不可用：
```bash
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
```

---

## 重要文档

- [v1.3 Main Integration Seal](docs/v1_3_main_integration_seal.md)
- [v1.2 Alpha Final Seal Manifest](docs/v1_2_alpha_final_seal_manifest.md)
- [v1.2 Alpha Command Reference](docs/v1_2_alpha_command_reference.md)
- [Public-Safe Evidence Strategy](docs/public_safe_evidence_strategy.md)
- [Public-Safe Tag Mapping](docs/public_safe_tag_mapping.md)
- [Large Evidence Archive Manifest](docs/large_evidence_archive_manifest.md)

---

## Tag / Evidence 策略

部分本地 sealed tag 未推送到 GitHub，因为其可达历史包含 373 MB SWE-bench 证据包，超出 GitHub 100 MB blob 大小限制。

仅推送公开安全的 tag。大证据包应通过 Release Asset 或外部冷存储发布，Git 仅保留清单和 SHA256 引用。

---

## Harness OS 不是

Harness OS **不是**模型提供商，不是通用编码框架，也不是云 SaaS 产品。

当前它是一个**本地优先的语义副驾驶和治理层**，用于 AI 辅助工程。
