# Harness OS 最终架构文档（Architecture v1.0）

基于本项目已整理来源：

- iii Harness / iii Workers
- Anthropic Harness Design
- Claude Agent SDK
- OpenAI Agents SDK
- LangGraph（仅借鉴状态机思想）
- Aider
- Continue
- OpenCode

并结合本轮讨论形成。

---

# 一、系统定位

Harness OS 不是：

```text id="xpa8ml"
聊天机器人
工作流编排器
Dify替代品
多Agent平台
RAG平台
```

Harness OS 是：

```text id="jfb3rc"
Codex 的 Project Operating System
```

作用：

```text id="wn7t47"
管理项目生命周期
管理上下文
管理状态
管理工具
管理权限
管理验证
管理交付
```

Codex：

```text id="bnc30o"
负责思考和执行
```

Harness：

```text id="n0hdlr"
负责项目运行环境
```

---

# 二、核心原则

## 单 Agent

禁止：

```text id="uke7xj"
Planner Agent
Research Agent
Coder Agent
Reviewer Agent
```

允许：

```text id="ab9zaf"
Codex
+
Skills
```

---

## 单模型

禁止：

```text id="y2rsb5"
Claude规划
Gemini搜索
Codex编码
```

允许：

```text id="7wiuuv"
一个主模型
```

所有：

```text id="gvqrb7"
总结
Review
Context理解
Decision
```

全部由同一个模型完成。

---

## Workspace First

项目状态永远存在：

```text id="eskjxw"
Workspace
```

而不是：

```text id="2ga9mz"
聊天历史
```

---

## Git First

长期状态来源：

```text id="5n9cuy"
Git Repo
```

不是：

```text id="fuy6t8"
Vector DB
```

---

# 三、系统总架构

```text id="8qqp8u"
Harness Runtime
│
├── Project Manager
│
├── Agent Runtime Adapter
│
├── Context System
│
├── State System
│
├── MCP Skill Layer
│
├── Governance System
│
├── Verification System
│
├── Observability System
│
└── Delivery System
```

---

# 四、Project Manager

负责：

```text id="o04kv8"
项目创建
项目打开
项目初始化
项目配置
项目迁移
项目恢复
```

接口：

```text id="i4ax6m"
create
open
clone
import
archive
restore
```

---

## create

```bash id="0wgrgg"
harness create my-project
```

自动：

```text id="5uv8qu"
创建Repo

初始化目录

初始化AGENTS.md

初始化.project/

注册skills

建立state
```

---

# 五、Workspace

项目运行容器。

结构：

```text id="5zu64y"
repo/
│
├── AGENTS.md
├── .project/
│   ├── state/
│   ├── tasks/
│   ├── decisions/
│   ├── reports/
│   ├── checkpoints/
│   └── context/
│
├── src/
├── docs/
├── tests/
└── ...
```

---

# 六、Agent Runtime Adapter

作用：

```text id="0vqhwr"
把Harness接到Codex
```

负责：

```text id="rwtveq"
Context输入

Tool暴露

Session恢复

Task执行
```

不负责：

```text id="fj8yrb"
推理
规划
编码
```

这些属于Codex。

---

# 七、Context System

整个系统核心。

负责：

```text id="y2qus1"
上下文发现
上下文压缩
上下文组合
上下文治理
```

---

## 输入

```text id="mwthey"
AGENTS.md

项目状态

当前任务

Git Diff

最近任务

测试结果

Workspace结构
```

---

## 输出

```text id="86v6pl"
Context Pack
```

结构：

```text id="q84rg0"
Task

Project Facts

Current State

Relevant Files

Relevant Decisions

Recent Changes

Constraints

Available Skills
```

---

# 八、State System

Claude Code 和 OpenAI Sessions 的融合。

作用：

```text id="x0p5xj"
保存项目运行状态
```

---

## State Tree

```text id="py8cf5"
Project

 ├─ Sessions

 ├─ Tasks

 ├─ Decisions

 ├─ Checkpoints

 └─ Reports
```

---

## Session

记录：

```text id="facxdo"
当前任务

运行历史

上下文摘要

状态快照
```

---

## Checkpoint

类似：

```text id="s88or2"
游戏存档
```

记录：

```text id="ouudiy"
Git状态

任务状态

Context状态

Skill状态
```

支持：

```text id="r8qjfh"
恢复
回滚
继续执行
```

---

# 九、MCP Skill Layer

Skill是Harness能力系统。

不是Agent。

---

## Filesystem Skill

能力：

```text id="37gwdr"
读文件
写文件
移动文件
创建文件
```

---

## Shell Skill

能力：

```text id="ikam02"
执行命令

运行测试

运行构建
```

---

## Git Skill

能力：

```text id="b8dxvp"
status

diff

branch

commit

merge

revert
```

---

## GitHub Skill

能力：

```text id="9q54rb"
PR

Issue

Review

Release
```

---

## Browser Skill

能力：

```text id="xa19ec"
文档浏览

Issue查看

网页分析
```

---

## Repo Scanner Skill

能力：

```text id="99plhq"
项目扫描

依赖分析

代码地图

符号发现
```

---

## Database Skill

能力：

```text id="irtyft"
SQLite

Postgres

MySQL
```

---

# 十、Governance System

治理层。

负责：

```text id="i4tns0"
权限

审批

预算

安全策略
```

---

## Approval Gate

拦截：

```text id="qsk1bi"
删除文件

修改AGENTS.md

修改架构

部署

推送Main
```

---

## Secret Policy

禁止：

```text id="p7khwb"
API Key泄露

Token泄露

密码写入日志
```

---

# 十一、Verification System

执行后必须验证。

---

## Lint

```text id="rnfx3h"
eslint

ruff

golangci-lint
```

---

## Typecheck

```text id="jrr5zf"
tsc

mypy
```

---

## Tests

```text id="qb2h4u"
unit

integration

e2e
```

---

## AI Review

Codex进行：

```text id="qllsqt"
风险分析

规范检查

缺失测试
```

---

# 十二、Observability System

来自 OpenAI Tracing 思想。

记录：

```text id="oz866r"
全部执行轨迹
```

---

## Events

```text id="cxpvfd"
任务开始

工具调用

文件修改

验证结果

审批事件
```

---

## Replay

支持：

```text id="fe53rq"
重放任务
```

查看：

```text id="9322bl"
Agent如何完成任务
```

---

## Run Report

生成：

```text id="3i74n9"
任务报告
```

包含：

```text id="if5pma"
目标

修改

验证

风险

下一步
```

---

# 十三、Delivery System

负责交付。

---

## Commit

自动生成：

```text id="yu3371"
commit message
```

---

## PR

自动生成：

```text id="2ka3z4"
PR Summary

Changed Files

Risks

Tests
```

---

## Release

生成：

```text id="dbwlso"
Release Notes
```

---

## Deploy

统一入口：

```bash id="klig3p"
harness deploy
```

---

# 十四、AGENTS.md

项目入口协议。

必须存在。

包含：

```text id="ejx0vr"
项目目标

架构约束

编码规范

运行方式

测试方式

审批规则

Skill说明

Context规则
```

Agent进入项目第一件事：

```text id="uz13i2"
读取AGENTS.md
```

---

# 十五、与开源项目映射

## Claude Code

借鉴：

```text id="6y1rb9"
Workspace模式

Permission模式

Tool模式

Session模式
```

不复制：

```text id="wn2keh"
产品实现
```

---

## Claude Agent SDK

借鉴：

```text id="u61ea5"
Hooks

MCP

Tool Runtime
```

---

## OpenAI Agents SDK

借鉴：

```text id="byjgst"
Sessions

Tracing

Guardrails

Tool Abstraction
```

---

## iii Harness

借鉴：

```text id="znwruq"
Harness即Backend

Runtime架构

Worker思想
```

---

## Aider

借鉴：

```text id="1wr9bc"
Git First

Repo First

单Agent
```

---

## Continue

借鉴：

```text id="wuthkx"
Codebase Awareness

Workspace理解
```

---

## LangGraph

仅借鉴：

```text id="91yoz9"
State Machine

Checkpoint
```

不采用：

```text id="4ci7y4"
Multi Agent Graph
```

---

# 十六、最终验收标准

项目达到以下能力才算完成。

---

## 项目管理

```text id="y6fr8t"
创建项目
打开项目
恢复项目
迁移项目
```

全部可用。

---

## Context

能够：

```text id="u5zb27"
自动构建Context Pack

控制Token

恢复历史任务
```

---

## State

支持：

```text id="7cqf6n"
Session

Checkpoint

Resume
```

---

## Skills

支持：

```text id="lx0rhs"
Filesystem

Shell

Git

GitHub

Browser

RepoScanner
```

---

## Governance

支持：

```text id="1zy9vw"
权限控制

审批

Secret保护
```

---

## Verification

支持：

```text id="in3ieo"
Lint

Typecheck

Tests

Review
```

---

## Observability

支持：

```text id="aze2o4"
日志

Trace

Replay

Run Report
```

---

## Delivery

支持：

```text id="t69bna"
Commit

PR

Release

Deploy
```

---

# 最终定义

Harness OS =

```text id="ddmpn8"
Workspace
+
Context
+
State
+
Skills
+
Governance
+
Verification
+
Observability
+
Delivery
```

Codex =

```text id="fd8r4a"
唯一执行Agent
```

整个系统最终目标不是构建一个 Agent 平台，而是：

```text id="ul1osc"
构建一个让 Codex 能长期维护、开发、交付项目的 Project Operating System。
```
