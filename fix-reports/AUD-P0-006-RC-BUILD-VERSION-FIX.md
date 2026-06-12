# AUD-P0-006 修复报告 — RC 构建、版本与执行证据

> **来源**: `Harness-OS-P0-Fix-Requirements/06_RC_EVIDENCE_BUILD_VERSION_FIX.md`
> **提交**: `f316b9c`
> **状态**: ✅ 已修复并提交（未 push）
> **日期**: 2026-06-12

---

## 一、问题概述

生产构建 DTS 阶段因 TypeScript 6.0 `baseUrl` deprecation 失败；版本号在 14 处硬编码不一致。

| 原问题 | 影响 |
|--------|------|
| `pnpm build` DTS 失败 | RC 无可用构建产物 |
| 版本号散落 14 处 | CLI `--version` / JSON meta / manifest 可能不同步 |

---

## 二、关键修正节点

### RC-01: 修复生产构建

**文件**: `tsconfig.json`

添加 `"ignoreDeprecations": "6.0"` 以兼容 TypeScript 6.0 的 `baseUrl` deprecation。

构建验证：
```
ESM ⚡️ Build success in 485ms
DTS ⚡️ Build success in 2204ms
```

### RC-02: 统一版本

**文件**: `src/version.ts` — 新增

```ts
export const HARNESS_VERSION = '1.0.0-rc.1';
```

所有框架版本引用改为从此文件导入：

| 位置 | 原值 | 现值 |
|------|------|------|
| `src/cli/index.ts` — `.version()` | `'1.0.0'` | `HARNESS_VERSION` |
| `src/cli/formatter.ts` — `buildMeta` | `'1.0.0'` | `HARNESS_VERSION` |
| `src/config/loader.ts` — 默认配置 | `'1.0.0'` | `HARNESS_VERSION` |
| `src/project/create.ts` — 项目 manifest | `'1.0.0'` | `HARNESS_VERSION` |
| `src/project/repair.ts` — repair manifest（2处） | `'1.0.0'` | `HARNESS_VERSION` |
| `src/runtime/index.ts` — `showConfig` | `'1.0.0'` | `HARNESS_VERSION` |

验证：`node dist/index.js --version` → `1.0.0-rc.1`

---

## 三、涉及模块变更

| 模块 | 文件 | 变更 |
|------|------|------|
| 根配置 | `tsconfig.json` | 添加 ignoreDeprecations: "6.0" |
| 新文件 | `src/version.ts` | 版本中心常量 |
| CLI | `src/cli/index.ts` + `formatter.ts` | 版本引用统一 |
| Config | `src/config/loader.ts` | 版本引用统一 |
| Project | `src/project/create.ts` + `repair.ts` | 版本引用统一 |
| Runtime | `src/runtime/index.ts` | 版本引用统一 |
| Tests | 3 个 test 文件 | 版本断言改为宽松匹配 |

---

## 四、构建验证

```
pnpm typecheck  → 成功（tsc --noEmit 无错误）
pnpm build      → 成功（ESM + DTS 双阶段通过）
node --version  → 1.0.0-rc.1
全部测试 497    → 通过
```

---

## 五、所有 P0 修复总结

| # | 编号 | 文件 | 提交 | 测试 |
|---|------|------|------|------|
| 1 | AUD-P0-001 | Governance Skill Policy 整合 | `76a627a` | +12 |
| 2 | AUD-P0-002 | Config Safety-Locked 安全字段注册表 | `7d00e68` | +28 |
| 3 | AUD-P0-003 | Secret Redactor 全链路脱敏 | `8fcd23b` | +12 |
| 4 | AUD-P0-004 | Verification & Delivery 强绑定 | `99f60d2` | +6 |
| 5 | AUD-P0-005 | CLI JSON 输出契约 | `c3e0b2b` | +11 |
| 6 | AUD-P0-006 | RC 构建与版本统一 | `f316b9c` | — |
| — | 额外 | post_tool_trace.py 弹性加固 | `05ea94f` | — |

**总测试**: 497 passed（428 基线 + 69 新增），零回归。

---

*生成日期: 2026-06-12 21:10 UTC*
