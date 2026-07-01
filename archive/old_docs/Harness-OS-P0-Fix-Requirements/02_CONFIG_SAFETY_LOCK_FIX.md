# P0-02 Config Safety-Locked 与 Immutable 策略修复需求

## 1. 目标

建立明确的安全配置合并语义，确保 Global、Project、Environment 和 CLI 等低层配置只能收紧安全策略，不能放宽默认或上层策略。

## 2. 涉及模块

- `src/config/loader.ts`
- `src/config/types.ts`
- `src/project/create.ts`
- `src/project/repair.ts`
- `src/governance/policy.ts`
- `src/delivery/guard.ts`
- `tests/unit/config.test.ts`
- `tests/integration/thin-harness-e2e.test.ts`
- `harness_os_docs/15_CONFIG_REFERENCE.md`

## 3. 修复节点

### CFG-01 建立安全字段注册表

为每个安全字段声明：

- 安全类型：boolean、enum、set、list、number。
- 默认值。
- 收紧方向。
- 是否 immutable。
- 允许覆盖的来源。

至少纳入：

- `governance.requireApprovalFor*`
- `governance.redactSecrets`
- `governance.defaultNetwork`
- `governance.allowWorkspaceOutsideAccess`
- `governance.dangerousCommands`
- `observability.secretRedaction`
- `delivery.requireApprovalFor*`
- `project.allowAutoPush`
- `project.allowAutoCommit`
- `project.protectedBranches`

### CFG-02 布尔安全语义

- approval/redaction 类字段：`true` 比 `false` 更严格。
- allow 类字段：`false` 比 `true` 更严格。
- 禁止使用统一的 `true → false` 规则处理所有 boolean。
- 放宽尝试必须保留原值并产生结构化 warning/event。

### CFG-03 Enum 安全语义

- `defaultNetwork`: `restricted` 不得被覆盖为 `allowed`。
- 未知 enum 值必须配置无效并 fail closed。
- 不得使用 `as any` 绕过运行时校验。

### CFG-04 集合与列表安全语义

- `dangerousCommands` 不得被清空或删除已有项目。
- lower layer 只能追加危险模式，不能移除。
- `protectedBranches` 只能追加，不能删除 `main`/`master`。
- 数组必须去重并规范化大小写。

### CFG-05 跨模块安全锁

- `observability.secretRedaction=false` 必须被拒绝。
- `delivery.requireApprovalForDeploy=false` 必须被拒绝。
- `project.allowAutoPush=true` 必须被拒绝，除非由明确的高权限 immutable policy 授权。
- 安全规则不能只检查 `governance` 根节点。

### CFG-06 Schema 验证

- 使用 Zod 或等价结构化 schema 验证每层配置。
- 非法配置不得静默忽略后继续执行高风险操作。
- 加载结果应区分 `valid`、`invalid-blocked` 和 `ignored-weaker`。

### CFG-07 来源与可审计性

- 每个最终配置值记录来源和被拒绝的 override。
- `harness config --json --show-source` 输出字段级 source。
- warning 中不得泄露配置里的秘密值。

### CFG-08 Immutable 策略

- 定义不可由项目、环境变量或 CLI 修改的字段。
- immutable 冲突必须阻断相关命令，而非仅提示。
- repair/init 不得重写或弱化已有更严格策略。

## 4. 测试矩阵

| 输入 | 期望 |
|---|---|
| `redactSecrets=false` | 拒绝，保留 true |
| `defaultNetwork=allowed` | 拒绝，保留 restricted |
| `allowWorkspaceOutsideAccess=true` | 拒绝 |
| `dangerousCommands=[]` | 拒绝删除默认项 |
| `allowAutoPush=true` | 拒绝 |
| `protectedBranches=[]` | main/master 仍保留 |
| `secretRedaction=false` | 拒绝 |
| `requireApprovalForDeploy=false` | 拒绝 |
| 增加危险命令 | 允许并合并 |
| 增加保护分支 | 允许并合并 |

## 5. 完成定义

- 所有 safety-locked 和 immutable 字段具有明确、测试化的收紧顺序。
- 任意配置层均不能复现审计中的放宽结果。
- 配置错误会阻断相关高风险流程。
- JSON 输出可说明最终值来源，但不暴露秘密。

