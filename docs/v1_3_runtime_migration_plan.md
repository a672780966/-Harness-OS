# v1.3 Runtime Migration Plan

**目标**: 让 Harness Copilot 在任何开发机器上可运行。

---

## 1. 当前支持路径

| 环境 | 状态 | 已验证 |
|------|:----:|:------:|
| Linux (Ubuntu 22.04+) | ✅ 完整支持 | 全部 755 tests |
| macOS (Intel/Apple Silicon) | ⚠️ 未封测 | 仅 Python 兼容性 |
| Windows native | ❌ 不推荐 | 潜在路径、编码、权限问题 |
| Windows WSL2 | ⚠️ 可运行但未封测 | 需验证依赖链 |

## 2. Windows native 风险

| 风险 | 严重度 | 影响 |
|------|:------:|------|
| `posixpath` vs `os.path` 混用 | 🟡 中 | 路径分割符错误 |
| `.harness/runtime/` 权限 | 🟡 中 | 文件写入可能失败 |
| ANSI color codes | 🟢 低 |终端渲染异常 |
| Git 和 Python 版本 | 🔴 高 | 需要单独安装 |
| Docker 依赖 (evaluation) | 🔴 高 | 无法在 native 跑 |
| Shell 脚本 (.sh) 依赖 | 🟡 中 | 无直接替代 |

**结论**: Windows native 延后到 v1.4+。

## 3. Windows WSL2 推荐路径

### 环境配置步骤

```bash
# 1. 安装 WSL2 (Ubuntu 22.04+)
wsl --install -d Ubuntu-22.04

# 2. 安装 Python 和依赖
sudo apt update && sudo apt install -y python3 python3-pip git

# 3. 克隆 Harness OS + 目标项目
git clone https://github.com/your/harness-os.git ~/harness-os
git clone <target-project> ~/projects/<name>

# 4. 安装 Python 依赖
cd ~/harness-os && pip install -r requirements.txt

# 5. 验证
cd ~/harness-os && python3 -m pytest tests/copilot/ -q
```

### 需要在 WSL2 上验证

- [ ] `harness copilot dashboard <path>` 输出路径以 `/mnt/c/` 开头时是否正常
- [ ] `.harness/runtime/` 是否可写入
- [ ] HTML shell 在 Windows 浏览器中打开路径格式
- [ ] Git diff 跨越 Windows/Linux 文件系统边界
- [ ] Provider guard 配置 (opencode CLI 路径)

## 4. 依赖检查清单

| 依赖 | 用途 | Linux | WSL2 | macOS |
|------|------|:----:|:----:|:-----:|
| Python 3.10+ | 核心运行时 | ✅ | ✅ | ✅ |
| Git 2.30+ | Git diff 分析 | ✅ | ✅ | ✅ |
| pip + requirements.txt | Python 依赖 | ✅ | ✅ | ✅ |
| opencode CLI (可选) | Provider canary | ⚠️ | ⚠️ | ⚠️ |
| Docker (可选) | Evaluation runs | ✅ | ✅ | ❌ |
| Node.js (可选) | Live server | ✅ | ✅ | ✅ |

## 5. CLI 安装方式

| 方式 | 优点 | 缺点 | 推荐 |
|------|------|------|:----:|
| 源码 `python3 -m harness.copilot.cli` | 零安装 | 必须 cd 到仓库 | 开发期 |
| `pip install -e .` | editable install | 需 setup.py | 活跃用户 |
| `pipx install .` | 隔离环境 | 更新需手动 | **推荐发行** |
| Standalone Docker image | 零依赖 | 镜像大 | v1.4 考虑 |

## 6. `.harness/runtime/` 目录迁移

当前: `PROJECT_ROOT/.harness/runtime/` (每个项目共享)

迁移计划:
- Phase 1: 保持每个项目独立
- Phase 2 (v1.3): 支持 `--runtime-dir` 参数
- Phase 3 (v1.4): 默认 `~/.harness/runtime/` 全局共享

当前存储内容:
```
.harness/runtime/
├── last_action_result.json    # 阶段执行状态
├── provider_health.json       # Provider 健康状态
└── (future) workspace.json    # 多项目工作区索引
```

## 7. Provider Guard 配置迁移

当前配置: `harness/copilot/provider_guard/config.py` (硬编码)

v1.3 目标:
1. 支持 `~/.harness/config.yaml` 全局配置
2. 环境变量覆盖优先级最高
3. per-project `.harness/provider.yaml` 覆盖

```yaml
# ~/.harness/config.yaml (v1.3 预期)
provider:
  default_model: "opencode-go/deepseek-v4-flash"
  connect_timeout: 10
  read_timeout: 90
  max_retries: 3
  canary:
    prompt: "OK"
    max_tokens: 10
    timeout: 45
```

## 8. Dogfood 项目目录结构

```
~/
└── projects/
    ├── Competitive-Product-Intelligence-System/
    │   └── .harness/             # (自动创建)
    │       ├── runtime/
    │       └── copilot_demo/
    ├── another-project/
    │   └── .harness/
    └── ...
```

## 9. Windows 机器上分析 CPIS 的完整流程

```powershell
# 1. 打开 WSL2 终端
# 2. 进入 Linux 工作区
cd ~/projects

# 3. 克隆目标项目 (首次)
git clone https://github.com/a672780966/Competitive-Product-Intelligence-System.git

# 4. 设置 Harness OS 路径
export HARNESS_PATH=~/harness-os
alias harness="python3 $HARNESS_PATH/harness/copilot/cli.py"

# 5. 运行分析
harness dashboard ~/projects/Competitive-Product-Intelligence-System --format markdown
harness shell ~/projects/Competitive-Product-Intelligence-System --out ~/projects/cpis-analysis/
harness live-dashboard ~/projects/Competitive-Product-Intelligence-System --out ~/projects/cpis-live/

# 6. 在 Windows 中打开 HTML
explorer.exe ~/projects/cpis-analysis/index.html
```
