# Harness OS Context Engineering Specification

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Single Agent, Single Model, Deterministic Context Pipeline

---

# 1. 定义

Context Engineering 是 Harness OS 的核心能力。

它的目标不是简单把所有文件塞给 Codex，而是把当前任务所需的项目事实、约束、代码、测试、历史状态、决策记录和工具能力，组织成一个可执行、可恢复、可审计的上下文包。

最终产物叫：

```text
Context Pack
```

Context Pack 是 Codex 每次执行任务前必须接收的项目输入。

---

# 2. 设计目标

Context Engineering 必须做到：

```text
1. 让 Codex 知道当前项目是什么
2. 让 Codex 知道当前任务是什么
3. 让 Codex 知道哪些文件相关
4. 让 Codex 知道已有架构约束
5. 让 Codex 知道可用 Skills
6. 让 Codex 知道当前 Git 状态
7. 让 Codex 知道测试和验证方式
8. 让 Codex 知道哪些操作需要审批
9. 控制上下文长度
10. 支持任务恢复和回放
```

Context Engineering 不做：

```text
向量数据库平台
多模型 rerank
独立 RAG 系统
GraphRAG
外部 memory repo
多 Agent 分工
```

---

# 3. 核心原则

## 3.1 Deterministic First

优先使用确定性方法构建上下文：

```text
文件路径匹配
Git diff
ripgrep
tree-sitter
package manifest
测试文件映射
任务记录
决策记录
```

语义判断由 Codex 完成，不引入单独 summarizer、embedding、reranker、classifier 模型作为核心依赖。

---

## 3.2 Workspace First

上下文来自项目工作区：

```text
AGENTS.md
.project/
src/
tests/
docs/
README.md
git state
```

不依赖聊天历史作为项目事实源。

---

## 3.3 Git First

上下文必须包含 Git 状态：

```text
当前分支
当前 diff
未提交文件
最近 commit
是否有用户未保存修改
```

Codex 不得在不了解 Git 状态的情况下修改项目。

---

## 3.4 Task First

上下文必须围绕当前任务构建。

不能默认读取整个仓库。

---

## 3.5 Recoverable Context

每次 Context Pack 必须保存到：

```text
.project/context/
```

以支持：

```text
resume
replay
debug
audit
rollback
```

---

# 4. Context System 总架构

```text
Context System
│
├── Source Collectors
│   ├── AGENTS.md Collector
│   ├── Project State Collector
│   ├── Task Collector
│   ├── Decision Collector
│   ├── Git Collector
│   ├── Repo Scanner Collector
│   ├── Test Collector
│   └── Report Collector
│
├── Relevance Engine
│   ├── Path Matcher
│   ├── Keyword Matcher
│   ├── Symbol Matcher
│   ├── Diff Matcher
│   └── Test Matcher
│
├── Context Assembler
│   ├── Required Context
│   ├── Task Context
│   ├── File Context
│   ├── Decision Context
│   ├── Verification Context
│   └── Skill Context
│
├── Context Budget Manager
│   ├── Token Estimator
│   ├── Priority Trimmer
│   └── Summary Selector
│
├── Context Snapshot Store
│   ├── JSON Snapshot
│   └── Markdown Snapshot
│
└── Context Reporter
    ├── Source List
    ├── Included Files
    ├── Excluded Files
    └── Risk Notes
```

---

# 5. Context Sources

## 5.1 Required Sources

每次任务必须读取：

```text
AGENTS.md
当前用户任务
git status
git diff
.project/state/project.md
.project/state/manifest.json
```

如果这些文件不存在，Harness 必须创建或修复项目结构。

---

## 5.2 Project State Sources

路径：

```text
.project/state/
```

推荐文件：

```text
.project/state/project.md
.project/state/manifest.json
.project/state/tech-stack.md
.project/state/repository-map.md
.project/state/current.md
```

用途：

```text
项目目标
技术栈
架构概况
当前状态
目录结构
运行方式
测试方式
```

---

## 5.3 Task Sources

路径：

```text
.project/tasks/
```

推荐结构：

```text
.project/tasks/
  active/
  completed/
  failed/
```

当前任务必须写入：

```text
.project/tasks/active/<task-id>.md
```

历史任务用于补充上下文，但优先级低于当前任务和当前 diff。

---

## 5.4 Decision Sources

路径：

```text
.project/decisions/
```

用于保存 ADR。

格式：

```text
ADR-0001-title.md
ADR-0002-title.md
```

Context Pack 必须包含与当前任务相关的决策。

---

## 5.5 Report Sources

路径：

```text
.project/reports/
```

用于读取最近任务报告、验证报告、失败报告。

Context Pack 可以包含最近相关失败，避免 Codex 重复犯错。

---

## 5.6 Code Sources

默认代码目录：

```text
src/
lib/
app/
packages/
services/
components/
tests/
```

Harness 不应默认读取所有文件，而应根据任务和索引选择。

---

## 5.7 Git Sources

必须收集：

```text
current branch
git status
git diff
untracked files
recent commits
```

推荐命令：

```bash
git status --short
git branch --show-current
git diff --stat
git diff
git log --oneline -n 10
```

---

# 6. Context Pack 标准结构

## 6.1 JSON Schema

```ts
export interface ContextPack {
  id: string
  projectId: string
  taskId: string
  runId: string
  createdAt: string

  task: TaskContext
  project: ProjectContext
  rules: RuleContext
  git: GitContext
  files: FileContext[]
  tests: TestContext[]
  decisions: DecisionContext[]
  recentRuns: RunSummaryContext[]
  verification: VerificationContext
  skills: SkillContext[]
  approvals: ApprovalContext
  budget: ContextBudget
  notes: ContextNote[]
}
```

## 6.2 Task Context

```ts
export interface TaskContext {
  title: string
  userInstruction: string
  normalizedInstruction: string
  taskType:
    | "feature"
    | "bugfix"
    | "refactor"
    | "test"
    | "docs"
    | "investigation"
    | "delivery"
    | "unknown"
  explicitFiles: string[]
  explicitCommands: string[]
  acceptanceHints: string[]
}
```

## 6.3 Project Context

```ts
export interface ProjectContext {
  name: string
  type: string
  primaryLanguage: string
  runtime: string
  packageManager?: string
  repositoryRoot: string
  architectureSummary?: string
  techStackSummary?: string
}
```

## 6.4 Rule Context

```ts
export interface RuleContext {
  source: "AGENTS.md"
  architectureRules: string[]
  codingRules: string[]
  testingRules: string[]
  securityRules: string[]
  deliveryRules: string[]
  forbiddenPatterns: string[]
}
```

## 6.5 Git Context

```ts
export interface GitContext {
  branch: string
  statusShort: string
  diffStat: string
  diffSummary?: string
  changedFiles: string[]
  untrackedFiles: string[]
  recentCommits: string[]
  hasUserChanges: boolean
}
```

## 6.6 File Context

```ts
export interface FileContext {
  path: string
  reason:
    | "explicit"
    | "git-diff"
    | "keyword-match"
    | "symbol-match"
    | "test-match"
    | "decision-reference"
    | "recent-task-reference"
  priority: number
  contentMode: "full" | "excerpt" | "summary" | "metadata-only"
  content?: string
  excerpt?: string
  summary?: string
  symbols?: string[]
}
```

## 6.7 Decision Context

```ts
export interface DecisionContext {
  id: string
  path: string
  title: string
  status: "proposed" | "accepted" | "rejected" | "superseded"
  summary: string
  relevanceReason: string
}
```

## 6.8 Skill Context

```ts
export interface SkillContext {
  name: string
  description: string
  allowed: boolean
  riskLevel: "low" | "medium" | "high"
  requiresApproval: boolean
}
```

## 6.9 Context Budget

```ts
export interface ContextBudget {
  maxTokens: number
  estimatedTokens: number
  reservedForResponse: number
  reservedForToolResults: number
  trimmingApplied: boolean
}
```

---

# 7. Context 构建流程

## 7.1 总流程

```text
1. Normalize Task
2. Load AGENTS.md
3. Load Project State
4. Inspect Git State
5. Scan Explicit Files
6. Discover Relevant Files
7. Match Tests
8. Load Decisions
9. Load Recent Reports
10. Build Context Candidates
11. Apply Priority Rules
12. Apply Context Budget
13. Assemble Context Pack
14. Save Snapshot
15. Start Codex Run
```

## 7.2 Normalize Task

输入：用户自然语言任务。输出：task title、task type、explicit files、explicit commands、acceptance hints。

## 7.3 Load AGENTS.md

必须提取项目目标、架构规则、编码规范、测试命令、审批规则、禁止模式、交付规则。如果缺失 AGENTS.md，则阻止任务执行并请求初始化项目。

## 7.4 Inspect Git State

必须在任何编辑前执行。收集当前分支、未提交修改、未跟踪文件、diff、最近 commit。如果发现用户已有未提交修改，Context Pack 必须标记 hasUserChanges = true，Codex 不得覆盖这些修改。

## 7.5 Discover Relevant Files

发现策略：用户显式提到的文件或目录、git diff 中已有修改文件、文件名关键词匹配、内容关键词匹配、symbol/import/export 关系、测试文件映射、最近任务引用、ADR 引用。

## 7.6 Match Tests

测试匹配规则：src/foo.ts -> tests/foo.test.ts；src/foo.ts -> src/foo.test.ts；components/Button.tsx -> components/Button.test.tsx；app/login/page.tsx -> app/login/page.test.tsx。

## 7.7 Load Decisions

仅加载相关 ADR。相关性来源包括任务关键词命中、文件路径命中、模块名称命中、技术栈命中、最近任务引用。

## 7.8 Build Context Candidates

每个候选上下文必须有 source path、source type、reason、priority、estimated tokens、content mode。

---

# 8. Priority Rules

Context 优先级：

```text
P0 必须包含
  当前用户任务
  AGENTS.md 摘要
  git status
  git diff stat
  当前 task state
  相关显式文件

P1 高优先级
  当前 diff 文件
  相关测试文件
  相关架构规则
  相关 ADR
  package manifest
  run/test commands

P2 中优先级
  最近完成任务
  失败报告
  repository map
  tech stack summary

P3 低优先级
  README
  docs
  长历史报告
  不相关代码片段
```

当 token 超预算时，按 P3 -> P2 -> P1 顺序裁剪。P0 不可裁剪，只能摘要化。

---

# 9. Content Modes

支持 full、excerpt、summary、metadata-only。full 适合小文件、用户明确指定文件、当前要编辑文件、测试文件。excerpt 适合大文件中的相关函数、类、配置段。summary 适合历史任务、长文档、长报告、旧 ADR。metadata-only 适合低相关文件、目录结构、索引项。

---

# 10. Context Budget

默认预算：max context budget 70%，reserved for Codex response 20%，reserved for tool results 10%。Token estimation 可使用 `estimatedTokens = Math.ceil(text.length / 4)`。裁剪顺序为删除 P3 metadata、压缩 P3 summary、删除 P2 older reports、将 P2 full 改为 summary、将 P1 full 改为 excerpt、保留 P0 但允许摘要化。不得删除当前任务、AGENTS.md 核心规则、git status、显式文件、审批规则。

---

# 11. Context Snapshot

每次构建 Context Pack 必须保存 JSON Snapshot 和 Markdown Snapshot。

路径：

```text
.project/context/<run-id>.json
.project/context/<run-id>.md
```

---

# 12. Markdown Context Pack Format

```markdown
# Context Pack: <run-id>

## Task

## Project

## Rules from AGENTS.md

## Git State

## Relevant Files

### <file path>

Reason:
Priority:
Content Mode:

```text
<content or excerpt>
```

## Related Tests

## Related Decisions

## Recent Reports

## Available Skills

## Approval Rules

## Context Budget

## Notes
```

---

# 13. Context Refresh

Context Pack 不是一次性静态对象。文件被修改、git diff 改变、测试失败、新增任务发现、审批被拒绝、Codex 请求更多上下文、运行时间过长、上下文明显过期时必须刷新。刷新后必须生成新版本 `.project/context/<run-id>-v2.json` 和 `.project/context/<run-id>-v2.md`。

---

# 14. Context Compression

Context Compression 不是独立模型任务。由 Codex 在 Harness 提供材料后完成摘要，Harness 负责选择需要压缩的材料、提供压缩目标、保存压缩结果、标记压缩来源。压缩结果必须包含来源路径。

---

# 15. Context and Memory Relationship

Project Memory 是 Context System 的一部分，不是独立系统。

```text
.project/state/
.project/tasks/
.project/decisions/
.project/reports/
.project/context/
```

不允许默认创建 memory-repo、knowledge-repo、vector-memory-service。

---

# 16. Context and Skills Relationship

Context Pack 必须告诉 Codex 当前可用 Skills，包括 skill name、what it can do、risk level、approval requirement、usage constraints。Codex 不能调用未在 Context Pack 中声明的 Skill。

---

# 17. Context and Governance Relationship

Context Pack 必须包含审批规则，包括哪些操作需要审批、哪些路径受保护、哪些命令被禁止、哪些命令需要确认、哪些 secrets 不能读取。

---

# 18. Context and Verification Relationship

Context Pack 必须包含验证方式，来源包括 AGENTS.md、package.json、Makefile、pyproject.toml、README、CI config。输出 lint command、typecheck command、test command、build command、e2e command。如果未发现测试命令，必须标记 `verification.commands.detected = false`。

---

# 19. Context Builder API

```ts
export interface ContextBuilder {
  build(input: BuildContextInput): Promise<ContextPack>
  refresh(input: RefreshContextInput): Promise<ContextPack>
  save(pack: ContextPack): Promise<ContextSnapshot>
}
```

```ts
export interface BuildContextInput {
  projectId: string
  runId: string
  taskId: string
  userInstruction: string
  workspacePath: string
  maxTokens: number
}
```

```ts
export interface RefreshContextInput {
  previousContextPackId: string
  reason:
    | "file-changed"
    | "test-failed"
    | "approval-denied"
    | "codex-request"
    | "budget-exceeded"
    | "manual"
}
```

---

# 20. Collector Interfaces

```ts
export interface ContextCollector<T> {
  name: string
  collect(input: CollectorInput): Promise<T>
}
```

Recommended collectors: AgentsMdCollector、ProjectStateCollector、TaskCollector、DecisionCollector、GitCollector、RepoScannerCollector、TestCollector、ReportCollector、SkillCollector、PolicyCollector。

---

# 21. Relevance Engine

```ts
export interface ContextCandidate {
  id: string
  type: "file" | "test" | "decision" | "report" | "state" | "git" | "skill"
  path?: string
  priority: 0 | 1 | 2 | 3
  score: number
  reason: string
  estimatedTokens: number
}
```

Scoring Rules：explicit file mention +100，current git diff +90，test match +80，symbol match +70，keyword match in filename +60，keyword match in content +50，recent task reference +40，decision reference +40，project state +30，old report +10。

---

# 22. Context Failure Modes

Missing AGENTS.md：block run，request project initialization。Dirty Git State：include warning，do not overwrite user changes，create checkpoint if editing。Context Over Budget：trim low priority，summarize medium priority，preserve P0。Unknown Test Command：infer from manifest，mark verification uncertainty，ask if necessary。Conflicting Instructions：pause，ask for confirmation，record conflict。

---

# 23. Context Report

每次 run 结束，Run Report 必须包含 Context Used、Context Excluded、Context Risks。

---

# 24. Implementation Checklist

P0：读取 AGENTS.md、git status、git diff、当前 task、project state、发现显式文件、发现 diff 文件、发现测试文件、生成 Context Pack JSON、生成 Context Pack Markdown、保存到 .project/context/。

P1：ripgrep 关键词检索、tree-sitter symbol index、ADR 相关性匹配、历史任务相关性匹配、Context Budget Manager、Context Refresh、Context Report。

P2：大文件 excerpt、自动 context summary、failure memory injection、multi-language test mapping、context replay UI。

---

# 25. Acceptance Criteria

1. 任意任务启动前都能生成 Context Pack
2. Context Pack 必须包含 AGENTS.md 核心规则
3. Context Pack 必须包含 Git 状态
4. Context Pack 必须包含当前任务
5. 修改任务必须包含相关文件和测试文件
6. Context Pack 必须保存 JSON 和 Markdown
7. Context Pack 必须可用于 resume
8. 超预算时必须可裁剪
9. 裁剪不能删除 P0 内容
10. Run Report 必须说明上下文来源
11. Codex 不能调用未声明 Skill
12. 高风险规则必须进入 Context Pack
13. 测试命令必须进入 Context Pack
14. 缺失 AGENTS.md 时必须阻止执行
15. 指令冲突时必须暂停确认

---

# 26. Final Definition

Context Engineering 在 Harness OS 中的最终定义：

```text
Context Engineering
=
把项目事实、任务目标、代码结构、历史状态、验证方式、权限规则和可用 Skills
转化为 Codex 可执行、可恢复、可审计的 Context Pack。
```

它是 Harness OS 的中枢，不是 RAG 附属功能。

Codex 能不能长期维护项目，关键取决于 Context Pack 是否正确、完整、克制、可恢复。
