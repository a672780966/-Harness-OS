# 第三轮修复 05：RC 工具链、测试稳定性与版本统一

## 执行提示词

读取本文件执行。只修 `AUD3-P0-005`，补回归测试，完成后提交；不 push，不打 tag，不启动 Thick Harness。

## 1. 修复目标

使 clean clone 可使用声明的 pnpm 安装、测试稳定通过、生产构建成功，并将 package、CLI、JSON meta 和 schema 的 RC 版本统一为新的候选版本。

## 2. 已确认问题

- 标准 `pnpm install --frozen-lockfile` 因 `devEngines.packageManager.version="^11.5.3"` 被 Corepack 拒绝。
- 全量测试连续复现为 `496 passed / 1 failed`。
- `listRunStates()` 仅按毫秒时间排序，同一时间戳时顺序不确定。
- `package.json` 为 `1.0.0`，CLI 为 `1.0.0-rc.1`。
- `v1.0.0-rc.1` 指向修复前提交，不得移动旧 tag。
- 最新 main 新增的 GitHub Actions 使用 `npm install` 和 `npx webpack`，与 pnpm/tsup 项目不符。

## 3. 允许修改范围

- `package.json`
- `pnpm-lock.yaml`
- `pnpm-workspace.yaml`
- `src/version.ts`
- 与版本输出直接相关的 manifest/schema
- `src/state/run.ts`
- 对应测试
- `.github/workflows/*`
- 必要的 build config

不得改动前四轮业务安全逻辑，也不得创建或移动 tag。

## 4. 详细修复节点

### RC3-01 Package Manager 声明

- 使用 Corepack 支持的精确 pnpm 版本声明，例如 `pnpm@11.5.3`。
- `packageManager` 与 `devEngines` 不得互相冲突。
- clean clone 下无需临时环境变量即可安装。
- lockfile 必须与声明版本兼容。

### RC3-02 测试稳定性

- 修复 run 排序的确定性。
- 时间戳相同时使用稳定 tie-breaker，例如单调序号或 run ID sequence。
- 不得通过在测试中添加固定 sleep 掩盖问题。
- 连续运行全量测试至少 3 次，全部 0 failure。

### RC3-03 版本统一

- 新目标版本使用 `1.0.0-rc.2`。
- package、CLI `--version`、JSON `meta.version`、runtime version、生成 manifest/schema 策略一致。
- 禁止继续把修复追加到旧 `v1.0.0-rc.1` 证据。
- 版本必须只有一个权威来源，其他位置通过构建或导入取得。

### RC3-04 构建

- `pnpm build` 在 Windows 和 CI Linux 环境均成功。
- ESM 与 DTS 均生成。
- `dist/index.js --version` 可运行。
- 构建不得依赖工作区外目录、全局包或未声明工具。

### RC3-05 CI

- GitHub Actions 使用 Corepack + pnpm frozen install。
- 执行 typecheck、test、build。
- Node matrix 只包含项目真实支持版本。
- 删除或修正 `npm install` + `npx webpack` 错误工作流。
- CI 不得启动 dev server 或 Thick Harness。

## 5. 必须新增的回归测试

1. 相同 `startedAt` 的 run 按确定性规则排序。
2. package version、CLI version、JSON meta version 一致。
3. build artifact 可执行。
4. package manager 声明可被 Corepack 解析。
5. 连续测试不会因时间戳碰撞失败。

## 6. 验收命令

必须从 clean clone 或等价干净目录执行：

```powershell
corepack enable
pnpm.cmd --version
pnpm.cmd install --frozen-lockfile
pnpm.cmd typecheck
pnpm.cmd test
pnpm.cmd test
pnpm.cmd test
pnpm.cmd build
node dist/index.js --version
node dist/index.js --json config
git status --short
```

预期：

- 三次测试均 0 failure。
- 版本均为 `1.0.0-rc.2`。
- build 成功。
- 除预期 ignored artifacts 外工作树无修改。

## 7. 完成定义

- clean install 无 workaround。
- 测试稳定 3/3 通过。
- Windows build 与 CI build 通过。
- 所有版本面统一为 rc.2。
- 旧 tag 未移动、未创建新 tag。

## 8. 提交要求

提交信息：

```text
fix: AUD3-P0-005 stabilize RC toolchain and version
```

完成报告必须列出 Node/pnpm/Git 版本、三次测试统计、构建产物、版本矩阵和 commit SHA。
