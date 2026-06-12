# 第三轮修复 02：Secret Redactor 全链路修复

## 执行提示词

读取本文件执行。只修 `AUD3-P0-002`，补回归测试，完成后提交；不 push，不打 tag，不启动 Thick Harness。

## 1. 修复目标

修复敏感字段值泄漏和键冲突，并确保 CLI、Report、Event、Trace、Context、Task、Checkpoint、Decision、Learning 与 Delivery 的所有输出边界统一脱敏。

## 2. 已确认问题

当前 `redactObject()` 将敏感键名改为 `[REDACTED]`，但继续保留原值。实测：

```json
{"password":"plain-secret","token":"second-secret"}
```

被转换为：

```json
{"[REDACTED]":"second-secret"}
```

这同时造成 secret 泄漏、字段覆盖和审计结构损坏。

## 3. 允许修改范围

- `src/governance/redactor.ts`
- CLI formatter
- Context、Observability、Verification、Delivery、Task、State、Decision、Learning 中的写入边界
- 对应 redactor/unit/integration tests

不得修改 Governance 决策、Verification 状态语义、Delivery gate 或版本号。

## 4. 详细修复节点

### SEC3-01 对象脱敏语义

- 保留字段名，敏感字段的值替换为 `[REDACTED]`。
- `password`、`secret`、`token`、`apiKey`、private key、credential 等键必须大小写不敏感。
- 嵌套对象、数组、Error、Map-like plain object 均递归处理。
- 多个敏感字段不得因重命名发生覆盖。
- 不得改变非敏感字段的数据类型和结构。

### SEC3-02 文本模式

- 覆盖短 token、普通密码、Bearer/JWT、GitHub/GitLab/Slack token、数据库 URL、云凭证、PEM/private key。
- 覆盖 JSON、YAML、`.env`、命令行参数、URL query、header 和 `key=value`。
- 禁止仅依赖长度阈值识别敏感键对应的值。
- 输出中不得出现 secret 前后缀片段。

### SEC3-03 统一输出 API

- 建立并强制使用 `safeJsonStringify()`、`safeWriteJson()`、`safeWriteText()`。
- 禁止安全相关模块直接 `JSON.stringify(untrusted)` 后写盘。
- 禁止将未经脱敏的用户输入、command、stdout、stderr、error stack 直接写入 CLI 或文件。
- 写入 API 应在序列化前深度脱敏，避免序列化后的结构误判。

### SEC3-04 必须覆盖的边界

- CLI JSON、pretty、quiet、stderr。
- Run/Verification/Delivery reports。
- Event JSONL 与 Trace JSON。
- Context Pack JSON 与 Markdown。
- Task、Run State、Checkpoint。
- Decision/ADR、Learning observations。
- commit message、PR body、guard reason。

### SEC3-05 审计真实性

- Event 返回值与实际落盘值不得产生“返回未脱敏、文件已脱敏”的歧义。
- `redacted` 标志只能在完成脱敏后设为 true。
- 脱敏失败必须阻止输出或写入安全占位错误，不得回退到原始内容。

## 5. 必须新增的回归测试

1. `{password, token, apiKey}` 保留三个键且三个值均为 `[REDACTED]`。
2. 嵌套数组和对象中的短密码、短 token 被脱敏。
3. CLI JSON stdout 可解析且不包含原 secret。
4. pretty、quiet 和 stderr 不包含原 secret。
5. Event、Trace、Context、Run Report、Verification Report、Delivery Report 文件不包含原 secret。
6. command、stdout、stderr 和 Error stack 中的 credential 被脱敏。
7. `.env`、YAML、URL query、Authorization header 被脱敏。
8. 非敏感字段值和结构保持不变。
9. 脱敏写入失败不会回退写入原始内容。

测试应使用唯一 canary：

```text
HARNESS_AUDIT_SECRET_7f31c9
```

测试结束后递归扫描临时项目，断言该字符串出现次数为 0。

## 6. 验收命令

```powershell
pnpm.cmd typecheck
pnpm.cmd test
pnpm.cmd build
```

另需运行一次仓库静态扫描，确认高风险模块没有未解释的直接写入：

```powershell
rg -n "writeFileSync|appendFileSync|JSON\.stringify|console\.(log|error)" src
```

## 7. 完成定义

- 敏感键名保留，敏感值统一替换。
- CLI / Report / Event / Trace / Context 全部通过 canary 测试。
- 不存在结构碰撞或明文回退。
- 全量测试 0 failure。

## 8. 提交要求

提交信息：

```text
fix: AUD3-P0-002 secret redaction boundaries
```

完成报告必须附 canary 扫描结果、覆盖边界列表、测试总数和 commit SHA。
