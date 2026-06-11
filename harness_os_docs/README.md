# Harness OS Documentation Index

Version: 2.0  
Project: Harness OS  
Purpose: Documentation entrypoint for Codex development

---

# 1. 文档总览

本目录包含 Harness OS 的核心工程规范文档。

Harness OS 的目标是构建一个：

```text
Codex-first
Single Agent
Single Model
Project Operating System
```

用于让 Codex 在受控、可恢复、可观测、可验证的项目环境中长期开发、维护和交付真实工程项目。

当前核心文档分为 12 份：

```text
01_ARCHITECTURE.md
02_CODEX_DEVELOPMENT_SPEC.md
03_AGENTS_MD_STANDARD.md
04_HARNESS_OS_DESIGN.md
05_CONTEXT_ENGINEERING.md
06_TASK_DECISION_PROJECT_MANAGER.md
07_MCP_SKILLS_SPEC.md
08_GOVERNANCE_SECURITY.md
09_VERIFICATION_OBSERVABILITY.md
10_DELIVERY_PIPELINE.md
11_ACCEPTANCE_CRITERIA.md
12_OPEN_SOURCE_REFERENCES.md
```

---

# 2. 推荐目录结构

```text
docs/
│
├── README.md
├── 01_ARCHITECTURE.md
├── 02_CODEX_DEVELOPMENT_SPEC.md
├── 03_AGENTS_MD_STANDARD.md
├── 04_HARNESS_OS_DESIGN.md
├── 05_CONTEXT_ENGINEERING.md
├── 06_TASK_DECISION_PROJECT_MANAGER.md
├── 07_MCP_SKILLS_SPEC.md
├── 08_GOVERNANCE_SECURITY.md
├── 09_VERIFICATION_OBSERVABILITY.md
├── 10_DELIVERY_PIPELINE.md
├── 11_ACCEPTANCE_CRITERIA.md
└── 12_OPEN_SOURCE_REFERENCES.md
```

---

# 3. 文档阅读顺序

## 3.1 给人类架构负责人阅读

```text
01_ARCHITECTURE.md
04_HARNESS_OS_DESIGN.md
02_CODEX_DEVELOPMENT_SPEC.md
05_CONTEXT_ENGINEERING.md
06_TASK_DECISION_PROJECT_MANAGER.md
07_MCP_SKILLS_SPEC.md
08_GOVERNANCE_SECURITY.md
09_VERIFICATION_OBSERVABILITY.md
10_DELIVERY_PIPELINE.md
11_ACCEPTANCE_CRITERIA.md
12_OPEN_SOURCE_REFERENCES.md
03_AGENTS_MD_STANDARD.md
```

目的：先理解系统边界，再理解模块设计，再理解实现规范、质量门、交付规则和项目协议。

## 3.2 给 Codex 开发时阅读

```text
02_CODEX_DEVELOPMENT_SPEC.md
04_HARNESS_OS_DESIGN.md
05_CONTEXT_ENGINEERING.md
06_TASK_DECISION_PROJECT_MANAGER.md
07_MCP_SKILLS_SPEC.md
08_GOVERNANCE_SECURITY.md
09_VERIFICATION_OBSERVABILITY.md
10_DELIVERY_PIPELINE.md
11_ACCEPTANCE_CRITERIA.md
03_AGENTS_MD_STANDARD.md
01_ARCHITECTURE.md
12_OPEN_SOURCE_REFERENCES.md
```

目的：先明确要开发什么，再理解模块如何实现，再读取具体协议、验收标准和参考边界。

## 3.3 给新项目初始化时使用

```text
03_AGENTS_MD_STANDARD.md
05_CONTEXT_ENGINEERING.md
06_TASK_DECISION_PROJECT_MANAGER.md
07_MCP_SKILLS_SPEC.md
08_GOVERNANCE_SECURITY.md
09_VERIFICATION_OBSERVABILITY.md
10_DELIVERY_PIPELINE.md
```

目的：生成业务项目内的 AGENTS.md，创建 .project/ 结构，建立任务、决策、上下文、Skill、治理、验证和交付规范。

---

# 4. 十二份核心文档说明

## 4.1 01_ARCHITECTURE.md

定义 Harness OS 的系统级架构，回答 Harness OS 是什么、它和 Codex 的关系是什么、系统由哪些核心模块组成、哪些属于 Harness、哪些不属于 Harness。

核心内容：系统定位、核心原则、总架构、Project Manager、Workspace、Agent Runtime Adapter、Context System、State System、MCP Skill Layer、Governance System、Verification System、Observability System、Delivery System、AGENTS.md、开源项目映射、最终验收标准。

关键结论：Harness OS = Codex 的 Project Operating System；Codex = 唯一执行 Agent；MCP Skills = Harness 内部工具层；Project Repo = 业务代码 + 项目本地状态；Git = 长期事实源。

## 4.2 02_CODEX_DEVELOPMENT_SPEC.md

交给 Codex 的主开发规范，回答 Codex 要开发什么、技术栈是什么、模块怎么拆、哪些能力必须实现、验收标准是什么、哪些开源项目可借鉴。

核心内容：项目愿景、核心原则、技术栈、系统架构、Workspace Architecture、Project Manager、AGENTS.md Protocol、Context System、State System、MCP Skill Layer、Governance System、Verification System、Observability System、Delivery System、Project Memory、开源项目映射、非目标、验收标准。

## 4.3 03_AGENTS_MD_STANDARD.md

定义每个被 Harness OS 管理的业务项目根目录下 `AGENTS.md` 应该如何编写。

核心内容：文件定位、优先级规则、必填章节、AGENTS.md Template、Project Identity、Project Goals、Architecture Rules、Repository Structure、Development Commands、Testing and Verification、Coding Standards、Context Rules、State and Memory Rules、Skill / Tool Rules、Permission and Approval Rules、Git and Delivery Rules、Security Rules、Task Completion Rules、Recovery Rules、Forbidden Patterns。

## 4.4 04_HARNESS_OS_DESIGN.md

详细说明 Harness OS 的系统设计、模块职责、运行流程、数据模型、安全设计和验收标准。

核心内容：Executive Summary、Design Goals、Non Goals、Core Principles、System Overview、Repository Boundary、Runtime Components、CLI / API Layer、Project Manager、Agent Runtime Adapter、Context System、State System、MCP Skill Runtime、Governance System、Verification System、Observability System、Delivery System、Project Local Files、Core Workflows、Data Model、Technology Stack、Open Source Reference Mapping、Security Design、Acceptance Criteria。

## 4.5 05_CONTEXT_ENGINEERING.md

定义 Harness OS 如何为 Codex 构建上下文。

核心内容：定义、设计目标、核心原则、Context System 总架构、Context Sources、Context Pack 标准结构、Context 构建流程、Priority Rules、Content Modes、Context Budget、Context Snapshot、Markdown Context Pack Format、Context Refresh、Context Compression、Context and Memory Relationship、Context and Skills Relationship、Context and Governance Relationship、Context and Verification Relationship、Context Builder API、Collector Interfaces、Relevance Engine、Context Failure Modes、Context Report、Implementation Checklist、Acceptance Criteria。

## 4.6 06_TASK_DECISION_PROJECT_MANAGER.md

定义项目、任务、决策三个治理模块的结构和流程。

核心内容：模块定位、设计目标、非目标、总体关系、Project Repository Layout、Project Manager Design、Project Lifecycle、Project Create Flow、Project Open Flow、Project Repair Flow、Project Manifest、Project State Markdown、Repository Map、Task Manager Design、Task Lifecycle、Task Create Flow、Task Types、Task Record Markdown、Task State JSON、Task Completion Flow、Task Directory Movement Rules、Decision Manager Design、Decision Lifecycle、Decision Types、ADR File Naming、ADR Markdown Template、Decision State JSON、Decision Creation Rules、Decision Acceptance Flow、Decision Supersede Flow、Manager APIs、Data Models、Event Model、Integration with Context System、Integration with Governance System、Integration with Delivery System、CLI Commands、File Protection Rules、Failure Handling、Reports、Implementation Checklist、Acceptance Criteria。

## 4.7 07_MCP_SKILLS_SPEC.md

定义 Harness OS 的 MCP Skills 工具能力层。

核心内容：模块定位、设计目标、非目标、核心原则、总体架构、Skill Registry、Skill Contract、Risk Model、Approval Rules、Skill Execution Flow、Filesystem Skill、Shell Skill、Git Skill、GitHub Skill、Browser Skill、Repo Scanner Skill、Test Runner Skill、Database Skill、Delivery Skill、Skill Events、Secret Redaction、Timeout and Cancellation、Context Pack Integration、Project Policy Integration、Error Handling、Implementation Checklist、Acceptance Criteria。

## 4.8 08_GOVERNANCE_SECURITY.md

定义 Harness OS 的治理、安全、审批、权限、路径保护、命令风险、Git 安全、Secret 脱敏、网络策略和交付安全规则。

核心内容：模块定位、设计目标、非目标、核心原则、Governance 总架构、Policy Sources、Policy Engine、Risk Levels、Approval Gate、Protected Path Policy、Shell Command Security、Git Safety Guard、Secret Security、Network Security、Dependency Security、Architecture Governance、Delivery Security、Audit and Observability、Violation Handling、Context Pack 集成、Skills 集成、Project/Task/Decision/Delivery 集成、Configuration、Implementation Checklist、Acceptance Criteria。

## 4.9 09_VERIFICATION_OBSERVABILITY.md

定义 Harness OS 的验证与可观测性体系。

核心内容：模块定位、设计目标、非目标、核心原则、总体架构、Verification System、Verification Plan、Verification Flow、Verification Result、Verification Report、Observability System、Event Model、Run Trace、Tool Call Recording、Context Usage Recording、File Change Recording、Approval Recording、Failure Recording、Replay、Run Report、系统集成、Data Retention、Redaction、Configuration、CLI Commands、Implementation Checklist、Acceptance Criteria。

## 4.10 10_DELIVERY_PIPELINE.md

定义 Harness OS 的交付流水线。

核心内容：模块定位、设计目标、非目标、核心原则、总体架构、Delivery Inputs、Delivery Outputs、Delivery Lifecycle、Delivery Plan、Delivery Guard、Commit Pipeline、Pull Request Pipeline、Release Pipeline、Deploy Pipeline、Rollback Pipeline、Delivery Report、Delivery Event Model、Delivery Config、与 Task/Verification/Governance/Observability/Decision/GitHub Skill 集成、Failure Handling、CLI Commands、Implementation Checklist、Acceptance Criteria。

## 4.11 11_ACCEPTANCE_CRITERIA.md

定义 Harness OS 的最终验收标准。

核心内容：文档定位、总体验收原则、系统级验收标准、CLI、Project Manager、AGENTS.md、Task Manager、Decision Manager、Context Engineering、MCP Skills、Governance and Security、Verification、Observability、Delivery Pipeline、State and Recovery、Codex Runtime Integration、Documentation、Thin Harness、Thick Harness、End-to-End 场景、Failure Acceptance、最终总体验收定义。

## 4.12 12_OPEN_SOURCE_REFERENCES.md

定义 Harness OS 可参考的开源项目、SDK、框架和工程模式，以及可借鉴和不可借鉴的边界。

核心内容：文档定位、总体原则、Reference Map、iii Harness / Workers、Claude Code / Claude Agent SDK、OpenAI Agents SDK、LangGraph、Aider、Continue、OpenCode、Dify、LLM Wiki / Markdown Knowledge Pattern、MCP Ecosystem、Reference-to-Module Matrix、Anti-Patterns、Adopted Patterns Summary、Implementation Guidance for Codex、Future Reference Intake Process、Final Definition。

---

# 5. 文档之间的依赖关系

```text
01_ARCHITECTURE.md
  ↓
04_HARNESS_OS_DESIGN.md
  ↓
02_CODEX_DEVELOPMENT_SPEC.md
  ↓
05_CONTEXT_ENGINEERING.md
  ↓
06_TASK_DECISION_PROJECT_MANAGER.md
  ↓
07_MCP_SKILLS_SPEC.md
  ↓
08_GOVERNANCE_SECURITY.md
  ↓
09_VERIFICATION_OBSERVABILITY.md
  ↓
10_DELIVERY_PIPELINE.md
  ↓
11_ACCEPTANCE_CRITERIA.md
  ↓
12_OPEN_SOURCE_REFERENCES.md
```

实现视角：

```text
03_AGENTS_MD_STANDARD.md
  feeds
05_CONTEXT_ENGINEERING.md

06_TASK_DECISION_PROJECT_MANAGER.md
  feeds
05_CONTEXT_ENGINEERING.md

07_MCP_SKILLS_SPEC.md
  feeds
Agent Runtime Adapter

08_GOVERNANCE_SECURITY.md
  governs
Skills / Delivery / Project State

09_VERIFICATION_OBSERVABILITY.md
  verifies and records
Runs / Tasks / Delivery

10_DELIVERY_PIPELINE.md
  packages
Verified changes

11_ACCEPTANCE_CRITERIA.md
  validates
All modules

12_OPEN_SOURCE_REFERENCES.md
  constrains
External pattern borrowing
```

---

# 6. 模块到文档映射

| 模块 | 主文档 | 辅助文档 |
|---|---|---|
| 总体架构 | 01_ARCHITECTURE.md | 04_HARNESS_OS_DESIGN.md |
| Codex 开发任务 | 02_CODEX_DEVELOPMENT_SPEC.md | 04_HARNESS_OS_DESIGN.md |
| 项目协议 | 03_AGENTS_MD_STANDARD.md | 05_CONTEXT_ENGINEERING.md |
| Harness Runtime | 04_HARNESS_OS_DESIGN.md | 02_CODEX_DEVELOPMENT_SPEC.md |
| Context System | 05_CONTEXT_ENGINEERING.md | 03_AGENTS_MD_STANDARD.md |
| Project Manager | 06_TASK_DECISION_PROJECT_MANAGER.md | 04_HARNESS_OS_DESIGN.md |
| Task Manager | 06_TASK_DECISION_PROJECT_MANAGER.md | 05_CONTEXT_ENGINEERING.md |
| Decision Manager | 06_TASK_DECISION_PROJECT_MANAGER.md | 03_AGENTS_MD_STANDARD.md |
| MCP Skills | 07_MCP_SKILLS_SPEC.md | 08_GOVERNANCE_SECURITY.md |
| Governance | 08_GOVERNANCE_SECURITY.md | 03_AGENTS_MD_STANDARD.md |
| Security | 08_GOVERNANCE_SECURITY.md | 07_MCP_SKILLS_SPEC.md |
| Verification | 09_VERIFICATION_OBSERVABILITY.md | 11_ACCEPTANCE_CRITERIA.md |
| Observability | 09_VERIFICATION_OBSERVABILITY.md | 06_TASK_DECISION_PROJECT_MANAGER.md |
| Delivery | 10_DELIVERY_PIPELINE.md | 08_GOVERNANCE_SECURITY.md |
| 验收标准 | 11_ACCEPTANCE_CRITERIA.md | 02_CODEX_DEVELOPMENT_SPEC.md |
| 开源参考 | 12_OPEN_SOURCE_REFERENCES.md | 01_ARCHITECTURE.md |

---

# 7. Codex 实现时的推荐任务拆分

## Epic 1: Repository Foundation

参考：02、04。任务：建立 TypeScript monorepo、CLI skeleton、docs、schemas、runtime、tests。

## Epic 2: Project Manager

参考：06、03。任务：harness create/open、.project 初始化、manifest 读写、project repair、repository map。

## Epic 3: AGENTS.md Template

参考：03。任务：AGENTS.md 模板、校验、缺失章节检查、修改审批保护。

## Epic 4: Context System

参考：05、06。任务：ContextBuilder、collectors、relevance engine、Context Pack JSON/Markdown、budget manager、snapshot。

## Epic 5: Task Manager

参考：06、05。任务：task create、lifecycle、markdown/json、active/completed/failed 移动、summary、run report link。

## Epic 6: Decision Manager

参考：06、03。任务：ADR 创建、编号、校验、状态流转、active decision 查询、审批元数据。

## Epic 7: Skill Runtime

参考：07、08。任务：skill contract、filesystem/shell/git/repo scanner skill、policy check、event log、redaction。

## Epic 8: Governance

参考：08、03。任务：policy engine、approval gate、protected files、dangerous command detection、secret redaction。

## Epic 9: Verification and Observability

参考：09、11。任务：命令检测、verification pipeline、report、event log、run trace、replay 数据结构。

## Epic 10: Delivery Pipeline

参考：10、08、09。任务：delivery plan、guard、commit message、PR body、delivery report、Git/GitHub 集成。

## Epic 11: Acceptance Gate

参考：11。任务：将验收标准转化为测试、E2E 场景、模块 checklist。

## Epic 12: Reference Guardrails

参考：12。任务：将外部参考的可借鉴/不可借鉴边界写入 Codex 开发流程和 ADR 流程。

---

# 8. 文件命名规范

所有文档使用两位数字编号：

```text
01_
02_
03_
```

规则：

```text
01-09: 核心设计与规范
10-19: 交付、验收、参考与扩展规范
20-29: 实现计划
30-39: 测试与验收细则
40-49: 开源参考与研究补充
```

---

# 9. 当前文档状态

| 编号 | 文档 | 状态 | 用途 |
|---|---|---|---|
| 01 | ARCHITECTURE | ready | 系统总架构 |
| 02 | CODEX_DEVELOPMENT_SPEC | ready | 给 Codex 的主开发规范 |
| 03 | AGENTS_MD_STANDARD | ready | 项目协议模板 |
| 04 | HARNESS_OS_DESIGN | ready | 系统设计文档 |
| 05 | CONTEXT_ENGINEERING | ready | 上下文工程规范 |
| 06 | TASK_DECISION_PROJECT_MANAGER | ready | 项目/任务/决策治理设计 |
| 07 | MCP_SKILLS_SPEC | ready | MCP Skills 工具能力层规范 |
| 08 | GOVERNANCE_SECURITY | ready | 治理与安全规范 |
| 09 | VERIFICATION_OBSERVABILITY | ready | 验证与可观测性规范 |
| 10 | DELIVERY_PIPELINE | ready | 交付流水线规范 |
| 11 | ACCEPTANCE_CRITERIA | ready | 最终验收标准 |
| 12 | OPEN_SOURCE_REFERENCES | ready | 开源参考边界 |

---

# 10. 最终索引定义

```text
01_ARCHITECTURE.md
  定义系统是什么。

02_CODEX_DEVELOPMENT_SPEC.md
  定义 Codex 要开发什么。

03_AGENTS_MD_STANDARD.md
  定义项目如何告诉 Codex 该怎么工作。

04_HARNESS_OS_DESIGN.md
  定义 Harness OS 内部如何运转。

05_CONTEXT_ENGINEERING.md
  定义 Codex 每次执行前应该看到什么。

06_TASK_DECISION_PROJECT_MANAGER.md
  定义项目、任务、决策如何被管理和持久化。

07_MCP_SKILLS_SPEC.md
  定义 Codex 可调用的受控工具能力。

08_GOVERNANCE_SECURITY.md
  定义 Codex 执行边界、安全规则和审批机制。

09_VERIFICATION_OBSERVABILITY.md
  定义任务如何验证、记录、追踪和回放。

10_DELIVERY_PIPELINE.md
  定义工程变更如何变成可交付产物。

11_ACCEPTANCE_CRITERIA.md
  定义 Harness OS 完成的最终验收门槛。

12_OPEN_SOURCE_REFERENCES.md
  定义外部项目只能如何被借鉴。
```

最终关系：

```text
Architecture
  governs
Harness OS Design

Harness OS Design
  decomposes into
Codex Development Spec

AGENTS.md Standard
  provides project rules to
Context Engineering

Task / Decision / Project Manager
  provides project state to
Context Engineering

MCP Skills
  provides governed tools to
Codex

Governance and Security
  constrains
Skills / Delivery / Project State

Verification and Observability
  verifies and records
Codex execution

Delivery Pipeline
  packages
verified changes

Acceptance Criteria
  validates
all modules

Open Source References
  constrains
external borrowing

Codex
  executes inside
Harness OS
```
