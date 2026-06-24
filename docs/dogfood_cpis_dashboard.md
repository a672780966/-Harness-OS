# Harness Code Copilot Dashboard — Competitive-Product-Intelligence-System

## 当前项目状态

- **项目**: Competitive-Product-Intelligence-System
- **路径**: `/home/ctyun/dogfood/Competitive-Product-Intelligence-System`
- **分支**: `main`
- **Agent 状态**: 待命
- **未提交变更**: 0 个文件
- **模块数**: 8
- **整体风险**: 🟡 中

## Agent 生命周期状态

💤 **状态**: 无事件 — 状态未知
- **置信度**: 0%
- **严重度**: low
- **阻塞合并**: 否 ✅

## 合并就绪度

🔴 **状态**: 禁止合并 🔴
  - Merge blocked: 8 blocking issue(s). 11 task card(s) still pending. 2 high-risk file(s) detected. Human review recommended.
  - **阻塞项** (8):
    - BLOCKED: High-risk changes in 'openclaw-plugins' (priority=high)
    - BLOCKED: High-risk changes in 'scripts' (priority=high)
    - BLOCKED: Critical: verify-deploy.sh (priority=critical)
    - BLOCKED: High-risk changes in 'openclaw-plugins' (level=high)
    - BLOCKED: High-risk changes in 'scripts' (level=high)
    - ... 还有 3 项
  - 需审查: 是
  - 待处理任务卡: 11
  - 高风险文件数: 2

## 最近修改

📝 **root** — Changed 1 file (+90/-52 lines)
  - 意图: 代码修改（混合）
  - 涉及文件: `CODEX-CLOUD-HANDOFF.md`

📝 **examples** — Added 69 lines across 5 files
  - 意图: 新增代码
  - 涉及文件: `examples/failed-publish-result.json, examples/partial-publish-result.json, examples/task-evidence.json, examples/task-publish.json, examples/valid-publish-result.json`

⚠️ **openclaw-plugins** — Changed 6 files (+362/-6 lines)
  - 意图: 测试用例变更
  - 涉及文件: `openclaw-plugins/cpis-json-gate/dist/index.js, openclaw-plugins/cpis-json-gate/dist/validator.js, openclaw-plugins/cpis-json-gate/install-on-lx.sh, openclaw-plugins/cpis-json-gate/openclaw.plugin.json, openclaw-plugins/cpis-json-gate/package.json ... 共 6 个文件`
  - ⚠ openclaw-plugins/cpis-json-gate/test/publish-validator.test.js: Substantial change (206 lines)

⚠️ **scripts** — Added 156 lines across 3 files
  - 意图: 新增代码
  - 涉及文件: `scripts/build-zip.sh, scripts/send-task-utf8.sh, scripts/verify-deploy.sh`
  - ⚠ scripts/verify-deploy.sh: Contains security/infra keyword: 'deploy'


## 重点模块

🟡 **backend** — 82 文件
  - 风险: 🟡 中
  - ⚠ `backend/tests/test_product_versioning.py`
  - ⚠ `backend/app/extractors/product_extractor.py`
  - ⚠ `backend/app/services/product_service.py`
  - ⚠ `backend/app/repositories/product_repository.py`
  - ⚠ `backend/app/models/product_version.py`
  - ⚠ `backend/app/models/product_evidence.py`
  - ⚠ `backend/app/models/product.py`

🟡 **frontend** — 22 文件
  - 风险: 🟡 中
  - ⚠ `frontend/src/features/products/ProductList.tsx`

🟡 **scripts** — 4 文件
  - 风险: 🟡 中
  - ⚠ `scripts/verify-deploy.sh`

✅ **openclaw-plugins** — 4 文件
  - 风险: ✅ 低

✅ **root** — 4 文件
  - 风险: ✅ 低

✅ **docs** — 1 文件
  - 风险: ❓ unknown

✅ **examples** — 5 文件
  - 风险: ❓ unknown

✅ **openclaw-agents-v2** — 6 文件
  - 风险: ❓ unknown


## 下一步建议

- 🟡 中优先级: Add tests for CLAUDE.md
  - 原因: Test coverage gap — add tests for untested source file
  - 文件: `CLAUDE.md`

- 🟡 中优先级: Add tests for CODEX-CLOUD-HANDOFF.md
  - 原因: Test coverage gap — add tests for untested source file
  - 文件: `CODEX-CLOUD-HANDOFF.md`

- 🟡 中优先级: Add tests for README.md
  - 原因: Test coverage gap — add tests for untested source file
  - 文件: `README.md`


# 推荐任务卡

**总计**: 11 张 | 待处理: 11 | 阻塞数: 3

🔴 **High-risk changes in 'openclaw-plugins'**
  - 类型: risk_alert | 优先级: 🟠 高优先级 | 状态: ⏳ 待处理
  - 模块: `openclaw-plugins`
  - 说明: Module 'openclaw-plugins' has 362+/6- changes classified as high risk.
  - ⛔ 阻塞合并

⚠️ **High risk: publish-validator.test.js**
  - 类型: risk_alert | 优先级: 🟠 高优先级 | 状态: ⏳ 待处理
  - 模块: `openclaw-plugins`
  - 目标文件: `openclaw-plugins/cpis-json-gate/test/publish-validator.test.js`
  - 说明: File 'openclaw-plugins/cpis-json-gate/test/publish-validator.test.js' flagged: Substantial change (206 lines)

🔴 **High-risk changes in 'scripts'**
  - 类型: risk_alert | 优先级: 🟠 高优先级 | 状态: ⏳ 待处理
  - 模块: `scripts`
  - 说明: Module 'scripts' has 156+/0- changes classified as high risk.
  - ⛔ 阻塞合并

🔴 **Critical: verify-deploy.sh**
  - 类型: risk_alert | 优先级: 🔴 紧急 | 状态: ⏳ 待处理
  - 模块: `scripts`
  - 目标文件: `scripts/verify-deploy.sh`
  - 说明: File 'scripts/verify-deploy.sh' has critical risk score (0.7).
  - ⛔ 阻塞合并

📋 **Review changes in 'root'**
  - 类型: fix_review | 优先级: 🟡 中优先级 | 状态: ⏳ 待处理
  - 模块: `root`
  - 说明: Changed 1 file (+90/-52 lines)

📋 **Review changes in 'examples'**
  - 类型: fix_review | 优先级: 🟡 中优先级 | 状态: ⏳ 待处理
  - 模块: `examples`
  - 说明: Added 69 lines across 5 files

📋 **Review changes in 'openclaw-plugins'**
  - 类型: fix_review | 优先级: 🟠 高优先级 | 状态: ⏳ 待处理
  - 模块: `openclaw-plugins`
  - 说明: Changed 6 files (+362/-6 lines)

📋 **Review changes in 'scripts'**
  - 类型: fix_review | 优先级: 🟠 高优先级 | 状态: ⏳ 待处理
  - 模块: `scripts`
  - 说明: Added 156 lines across 3 files

📋 **Add tests for CLAUDE.md**
  - 类型: fix_test | 优先级: 🟡 中优先级 | 状态: ⏳ 待处理
  - 模块: `root`
  - 目标文件: `CLAUDE.md`
  - 说明: Add tests for CLAUDE.md

Reason: Test coverage gap — add tests for untested source file

📋 **Add tests for CODEX-CLOUD-HANDOFF.md**
  - 类型: fix_test | 优先级: 🟡 中优先级 | 状态: ⏳ 待处理
  - 模块: `root`
  - 目标文件: `CODEX-CLOUD-HANDOFF.md`
  - 说明: Add tests for CODEX-CLOUD-HANDOFF.md

Reason: Test coverage gap — add tests for untested source file

📋 **Add tests for README.md**
  - 类型: fix_test | 优先级: 🟡 中优先级 | 状态: ⏳ 待处理
  - 模块: `root`
  - 目标文件: `README.md`
  - 说明: Add tests for README.md

Reason: Test coverage gap — add tests for untested source file


## 证据包

- **包 ID**: `pack_a33d26e8274d`
- **总证据数**: 0
- **通过**: 0
- **失败**: 0
- **完整性校验**: `87f0c3bc2a54a759...`

## 等待陪伴

⚪ Agent 待命中。等待陪伴模式未激活。

---
*生成时间: 2026-06-23T11:12:56.770399+00:00*
