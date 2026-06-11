# Harness OS Acceptance Criteria

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: A Harness OS feature is complete only when it is usable, governed, verified, observable, and recoverable

---

# 1. 文档定位

本文件定义 Harness OS 的验收标准，用于判断 Harness OS 是否已经达到可交付状态。

覆盖 Project Manager、Task Manager、Decision Manager、Context Engineering、MCP Skills、Governance and Security、Verification and Observability、Delivery Pipeline、AGENTS.md Standard、State and Recovery、Codex Runtime Integration、Documentation。

本文件不是开发计划，也不是功能清单，而是最终验收门槛。

---

# 2. 总体验收原则

Harness OS 的任何模块只有同时满足以下条件，才算完成：

```text
1. 可运行
2. 可配置
3. 可验证
4. 可观测
5. 可恢复
6. 可治理
7. 可审计
8. 可交付
```

如果某个模块只能在 happy path 工作，但无法记录状态、无法恢复、无法审批、无法报告，则不算完成。

---

# 3. 系统级验收标准

## 3.1 Architecture Acceptance

```text
1. Codex 是唯一执行 Agent
2. 系统核心不得引入 multi-agent orchestration
3. 系统核心不得引入 model router
4. Skills 必须是工具，不得变成 Agent
5. Harness 负责 workspace、context、state、skills、governance、verification、observability、delivery
6. Codex 负责 reasoning、coding、review、execution、summary
7. Git 必须作为长期事实源
8. .project/ 必须作为项目本地状态目录
9. AGENTS.md 必须作为项目操作协议
10. 所有高风险操作必须通过 Governance
```

## 3.2 Repository Acceptance

```text
1. 清晰的 monorepo 或模块化目录结构
2. CLI 入口
3. Runtime 核心模块
4. Skills 目录
5. Schemas 目录
6. Templates 目录
7. Docs 目录
8. Tests 目录
9. 可运行的开发命令
10. 可运行的测试命令
```

推荐结构：

```text
harness-os/
  docs/
  src/
    cli/
    runtime/
    project/
    task/
    decision/
    context/
    skills/
    governance/
    verification/
    observability/
    delivery/
    state/
  templates/
  schemas/
  tests/
  package.json
```

---

# 4. CLI 验收标准

必须支持：`harness create <name>`、`harness open <path>`、`harness run "<task>"`、`harness resume <run-id>`、`harness status`、`harness verify`、`harness report <run-id>`、`harness deliver`。

还应支持：`harness repair`、`harness checkpoint`、`harness rollback <checkpoint-id>`、`harness task list`、`harness decision list`、`harness skills list`、`harness events <run-id>`、`harness replay <run-id>`。

验收条件：每个命令有帮助信息；失败返回可读错误；高风险命令触发审批；执行写入事件日志；CLI 不得绕过 Runtime 直接修改受保护文件。

---

# 5. Project Manager 验收标准

```text
1. harness create 可以创建新项目
2. harness open 可以打开已有项目
3. 新项目必须包含 AGENTS.md
4. 新项目必须包含 .project/ 目录
5. .project/ 必须包含 state、tasks、decisions、reports、checkpoints、sessions、context
6. manifest.json 必须可读写
7. project.md 必须可生成
8. tech-stack.md 必须可生成或标记 unknown
9. repository-map.md 必须可生成
10. 缺失 .project/ 子目录时 repair 可以修复
11. 缺失 AGENTS.md 时必须阻止 run
12. Project Manager 不得覆盖已有 AGENTS.md，除非审批
13. Project Manager 必须读取 git status
14. Project Manager 必须生成 project events
15. Project state 必须能进入 Context Pack
```

---

# 6. AGENTS.md 验收标准

必须包含 Project Identity、Project Goals、Architecture Rules、Repository Structure、Development Commands、Testing and Verification、Coding Standards、Context Rules、State and Memory Rules、Skill / Tool Rules、Permission and Approval Rules、Git and Delivery Rules、Security Rules、Task Completion Rules。

验收条件：Codex run 启动前必须读取；缺失时阻止任务执行；缺失章节时警告或 repair；修改必须审批；Context Pack 必须包含核心规则；与用户指令冲突时必须暂停确认。

---

# 7. Task Manager 验收标准

```text
1. 每个用户任务必须生成 task id
2. 每个任务必须生成 Markdown task record
3. 每个任务必须生成 JSON task state
4. 任务必须有明确 lifecycle
5. 任务必须关联 run id
6. 任务必须关联 Context Pack
7. 任务必须关联 checkpoint
8. 任务必须记录 changed files
9. 任务必须记录 verification status
10. 任务必须记录 risks
11. 任务完成必须生成 summary
12. 任务失败必须生成 failure report
13. 完成任务必须移动到 .project/tasks/completed/
14. 失败任务必须移动到 .project/tasks/failed/
15. 任务状态必须可恢复
```

生命周期至少支持 created、ready、running、blocked、paused、verifying、completed、failed。

---

# 8. Decision Manager 验收标准

```text
1. Codex 可以创建 proposed ADR
2. ADR 文件必须有递增编号
3. ADR 必须有 Markdown 文件
4. ADR 必须有 JSON state
5. ADR 必须支持 proposed、accepted、rejected、superseded
6. accepted ADR 必须经过审批
7. accepted ADR 不能无审批修改
8. supersede accepted ADR 必须审批
9. active decisions 必须可被 Context System 读取
10. superseded ADR 不得作为 active constraint
11. 架构变更必须生成或更新 ADR
12. 重大技术变更必须生成或更新 ADR
13. Decision events 必须进入 Observability
14. Delivery 包含架构变更时必须检查相关 ADR
```

---

# 9. Context Engineering 验收标准

```text
1. 任意 run 启动前必须生成 Context Pack
2. Context Pack 必须包含当前任务
3. Context Pack 必须包含 AGENTS.md 核心规则
4. Context Pack 必须包含 git status
5. Context Pack 必须包含 git diff 或 diff summary
6. Context Pack 必须包含 relevant files
7. Context Pack 必须包含 related tests
8. Context Pack 必须包含 relevant decisions
9. Context Pack 必须包含 available skills
10. Context Pack 必须包含 approval rules
11. Context Pack 必须包含 verification commands 或 uncertainty
12. Context Pack 必须保存 JSON snapshot
13. Context Pack 必须保存 Markdown snapshot
14. Context Pack 必须可用于 resume
15. Context Pack 必须可用于 replay
16. 超预算时必须裁剪低优先级内容
17. P0 内容不得被删除
18. Codex 不得调用 Context Pack 未声明的 Skill
19. Context refresh 必须生成新版本
20. Run Report 必须说明 Context Used
```

---

# 10. MCP Skills 验收标准

```text
1. 每个 Skill 必须有 manifest
2. 每个 Tool 必须有 input schema
3. 每个 Tool 必须有 output schema
4. 每个 Tool 必须有 risk level
5. 每个 Tool 必须声明是否 requires approval
6. Skill Registry 必须可列出 enabled skills
7. Project manifest 必须可配置 enabled / disabled skills
8. Codex 只能调用 Context Pack 声明的 Skills
9. 每次 Skill 调用必须经过 Policy Engine
10. 每次 Skill 调用必须记录 event
11. Skill 输出必须经过 Secret Redactor
12. Skill 失败必须返回 recoverable 信息
13. Skill 调用必须可用于 replay
14. Skill 不得自行推理或规划
15. Skill 不得绕过 Governance
```

Core Skill Acceptance：P0 必须实现 Filesystem、Shell、Git、Repo Scanner；P1 应实现 GitHub、Test Runner、Delivery、Browser；P2 可实现 Database、Advanced Symbol Scanner、Remote Skill Registry、Custom Project Skills。

Filesystem Skill：限制 workspace 内路径，阻止 path/symlink escape，read_file/list_dir/search_text/write_file/edit_file 可用，delete_file/修改 AGENTS.md/修改 accepted ADR 必须审批，写操作记录 diff summary。

Shell Skill：设置 cwd/timeout，记录 stdout/stderr 摘要和 exit code，危险命令审批或阻止，sudo/curl|sh/wget|sh 默认禁止，输出脱敏，事件进入 Observability。

Git Skill：git status/diff/log/branch 可用，编辑前读取 status，不覆盖用户未提交修改，commit 前有 verification result，push main 审批，force push 默认禁止，reset hard 和 clean -fd 审批。

---

# 11. Governance and Security 验收标准

```text
1. 所有 Skill 调用必须经过 Policy Engine
2. 高风险操作必须进入 Approval Gate
3. Policy Engine 必须返回 allow、deny 或 requires-approval
4. Approval Request 必须记录 reason、risk、affected paths
5. 修改 AGENTS.md 必须审批
6. 修改 accepted ADR 必须审批
7. 删除文件必须审批
8. 新增重大依赖必须审批
9. push main 必须审批
10. deploy 必须审批
11. force push 默认禁止
12. Shell 命令必须支持风险分类
13. 危险命令必须阻止或审批
14. 文件操作必须限制在 workspace 内
15. symlink escape 必须阻止
16. secrets 必须 redacted
17. .env 不得进入 Context Pack
18. Governance events 必须进入 Observability
19. Violation 必须阻止执行并写入报告
20. Context Pack 必须包含治理摘要
21. 架构变更必须进入 Decision Manager
22. 任务完成前必须输出风险摘要
```

---

# 12. Verification 验收标准

```text
1. 每个代码任务完成前必须生成 verification result
2. verification result 必须绑定 task id
3. verification result 必须绑定 run id
4. 验证命令必须从 AGENTS.md / manifest / package files / Makefile / CI / README 中发现
5. 不得凭空编造验证命令
6. lint 可运行时必须运行
7. typecheck 可运行时必须运行
8. tests 可运行时必须运行
9. build 可运行且相关时必须运行
10. 验证失败不得标记任务 completed
11. 验证 skipped 必须说明原因
12. stdout/stderr 必须有摘要
13. verification report 必须写入 .project/reports/verification/
14. Verification status 必须支持 passed、failed、partial、skipped、blocked
15. Delivery 必须读取 verification result
```

---

# 13. Observability 验收标准

```text
1. 每个 run 必须有 event log
2. 每个 run 必须有 run trace
3. Event log 必须使用 JSONL 或等价可追加格式
4. Skill call 必须记录
5. Context Pack 使用必须记录
6. 文件变更必须记录
7. Git 操作必须记录
8. 审批事件必须记录
9. 安全事件必须记录
10. 验证事件必须记录
11. Delivery 事件必须记录
12. Run Report 必须生成
13. Verification Report 必须生成
14. Delivery Report 必须可关联
15. Replay 必须能重建执行过程
16. Secrets 必须 redacted
17. Failure 必须包含 recovery path
18. Task record 必须引用 run report
19. Observability 不能绕过 Governance
```

---

# 14. Delivery Pipeline 验收标准

```text
1. 没有 verification result 不得交付
2. verification failed 不得交付
3. run report 缺失不得创建 PR
4. commit 前必须读取 git status
5. commit 前必须读取 git diff
6. commit message 必须可生成
7. PR body 必须可生成
8. PR body 必须包含任务、变更、验证、风险、报告
9. release 必须审批
10. deploy 必须审批
11. rollback deploy 必须审批
12. push main 必须审批
13. force push 默认禁止
14. Delivery Report 必须生成
15. Delivery Event 必须记录
16. Delivery 必须读取 Task Manager 状态
17. Delivery 必须读取 Verification Result
18. Delivery 必须经过 Governance
19. 部署必须有 rollback plan
20. 失败交付必须写 failure details
21. 交付不得绕过 Git
22. GitHub Skill 不得自行决策
23. 架构变更交付必须关联 ADR
24. Delivery Report 必须可被 Run Report 引用
```

---

# 15. State and Recovery 验收标准

```text
1. 每个 run 必须有 run state
2. 每个 task 必须有 task state
3. 每个 session 必须有 session state
4. 高风险操作前必须创建 checkpoint 或确认可恢复
5. checkpoint 必须记录 git status
6. checkpoint 必须记录 current branch
7. checkpoint 必须记录 changed files
8. checkpoint 必须记录 context summary
9. checkpoint 必须记录 last successful step
10. failed run 必须可读取 recovery path
11. paused run 必须可 resume
12. rollback 必须经过审批
13. restore checkpoint 必须记录事件
14. Context Pack 必须支持恢复
15. Event log 必须支持 replay
```

---

# 16. Codex Runtime Integration 验收标准

```text
1. 能启动 Codex run
2. 能向 Codex 注入 Context Pack
3. 能向 Codex 暴露可用 Skills
4. 能接收 Codex tool call
5. 能把 tool call 转给 Skill Runtime
6. 能把 Skill result 返回给 Codex
7. 能处理 approval-required 状态
8. 能处理 blocked 状态
9. 能处理 failed 状态
10. 能处理 cancellation
11. 能处理 resume
12. 能记录 model input summary
13. 能记录 model output summary
14. 不得自行执行推理
15. 不得引入第二 Agent
16. 不得引入第二模型作为核心依赖
```

---

# 17. Documentation 验收标准

Docs 必须包含 01_ARCHITECTURE.md 到 11_ACCEPTANCE_CRITERIA.md，可选扩展 12_OPEN_SOURCE_REFERENCES.md。

文档验收条件：docs/README.md 索引所有文档；每份文档说明定位、非目标、验收标准；文档命名、模块名称一致；核心原则不冲突；Codex 开发前读取 02，模块实现前读取对应模块文档。

---

# 18. Thin Harness 最小可交付验收

必须具备 CLI、Project create/open、AGENTS.md 注入和校验、`.project/` 结构、Task Manager 基础生命周期、Context Pack、Filesystem/Shell/Git/Repo Scanner Skill、Policy Engine、Approval Gate、Secret Redaction、Verification、Event Log、Run Report、Checkpoint、Delivery Report。

不要求 GitHub PR 自动创建、完整 Browser Skill、完整 Database Skill、Dashboard、Remote approval service、Advanced replay UI、Policy packs、Team workflow。

---

# 19. Thick Harness 完整形态验收

在 Thin Harness 基础上增加 GitHub Skill、Browser Skill、Test Runner Skill、Delivery Skill、Database Skill 可选、Decision Manager 完整 ADR 生命周期、Replay 命令、Trace 聚合、完整 commit/PR/release/deploy、Governance policy config、Network policy、Dependency risk policy、Failure diagnosis、Context Refresh、Context Budget Manager、Repository symbol index、Multi-project registry、Project archive/restore、完整文档、核心路径测试覆盖。

---

# 20. End-to-End 验收场景

创建项目：`harness create demo` 后 AGENTS.md、`.project/`、manifest.json、project.md、repository-map.md、initial checkpoint、project.created event 存在。

打开项目：`harness open ./demo` 后读取 manifest、刷新 repository map、读取 git status、输出 project open summary。

执行任务：`harness run "修复登录按钮 loading 状态"` 后创建 task record、Context Pack、Codex run，记录 Skill calls、文件修改、verification、run report，task 移动到 completed 或 failed。

高风险审批：Codex 尝试修改 AGENTS.md 时 Policy Engine 返回 requires-approval，Approval Gate 创建 request，审批前不执行，approval event 被记录。

验证失败：tests failed 时 verification status = failed，task 不得 completed，生成 failure report，保存 checkpoint，记录 recovery path。

交付：task completed 且 verification passed，`harness deliver --pr` 读取 verification result/run report，生成 PR body，经过 Governance 检查，创建或准备 PR，写 delivery report。

恢复：run 被中断，`harness resume <run-id>` 读取 run state、checkpoint、context snapshot、task state 并继续 Codex run。

---

# 21. Failure Acceptance

系统必须正确处理 missing AGENTS.md、invalid manifest、dirty git conflict、context over budget、skill timeout、approval denied、policy denied、test failed、build failed、secret detected、workspace path escape、dangerous command、delivery blocked、PR creation failed、deploy failed、checkpoint restore failed。

每个失败必须阻止错误操作、记录事件、写入报告、提供原因和恢复建议，不谎称成功。

---

# 22. 最终总体验收定义

Harness OS 可以让 Codex 在真实项目中打开项目、读取项目协议、构建上下文、创建任务、调用受控 Skills、修改代码、记录状态、处理审批、执行验证、生成报告、准备交付、失败后恢复。

同时必须不多 Agent、不多模型路由、不绕过 Governance、不跳过 Verification、不丢失状态、不泄露 Secrets、不覆盖用户修改、不无审批部署、不把聊天历史当项目事实源。

最终一句话：Harness OS 只有在 Codex 的每一次项目执行都可治理、可验证、可观测、可恢复、可交付时，才算完成。
