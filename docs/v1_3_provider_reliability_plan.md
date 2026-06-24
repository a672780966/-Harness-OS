# v1.3 Provider Reliability Plan

**问题**: Provider `opencode-go/deepseek-v4-flash` 被标记为 `degraded`。
**诊断**: `upstream_model_inference_timeout_or_sse_hang` (endpoint 可达，但推理超时)。

---

## 1. 当前 degraded 问题详情

| 属性 | 值 |
|------|-----|
| Provider | opencode-go/deepseek-v4-flash |
| State | `degraded` (2 consecutive failures) |
| Failure type | `timeout` |
| Endpoint | Reachable (DNS/TLS/HTTP < 1.2s) |
| Minimal canary | "OK" (max_tokens=10) timed out after 30s |
| Impact | Long implementation phases blocked |
| Not impacted | Local readonly features |

## 2. 定位问题

诊断结论:

```
api_healthcheck: pass
failure_type: upstream_model_inference_timeout_or_sse_hang
```

不是 DNS/TLS/HTTP 问题，不是配额问题，是**上游推理延迟不稳定**（偶尔 > 30s）。

## 3. 当前 Provider Guard 策略

```
connect_timeout: 10s
read_timeout: 90s
max_retries: 3
retry_backoff: exponential + jitter
canary_prompt: "OK"
canary_max_tokens: 10
canary_timeout: 45s
degrade_threshold: 2 consecutive failures
cooldown: 120s
```

## 4. Fallback Model 方案

### 方案 A: 多 Provider 配置 (推荐入 v1.3)

```yaml
# ~/.harness/config.yaml
providers:
  primary:
    model: "opencode-go/deepseek-v4-flash"
    timeout: 45
    max_retries: 3
  fallback:
    model: "opencode/deepseek-v4-flash-free"
    timeout: 60
    max_retries: 5
  readonly_fallback:
    model: ""  # 不使用 model 的本地模式
    local_only: true
```

自动回退逻辑:
1. 先尝试 primary
2. primary degraded → 尝试 fallback
3. fallback 也 degraded → 切换 readonly_fallback (只允许本地命令)
4. cooldown 后自动重试 primary

### 方案 B: 超时参数放宽 (低风险, 可立即调整)

```bash
# 通过环境变量临时放宽
HARNESS_PROVIDER_CANARY_TIMEOUT=90 \
HARNESS_PROVIDER_READ_TIMEOUT=180 \
python3 -m harness.copilot.cli live-server .
```

### 方案 C: 本地模型 (v1.4+, 高投入)

可以用 Ollama / llama.cpp 运行本地模型做 canary，
但 v1.3 不涉及。

## 5. 推荐 v1.3 方案

**推荐**: 方案 A (多 Provider 配置), 配合方案 B (环境变量放宽)

```python
# provider_guard/config.py 扩展 (v1.3)
# 新增:
class ProviderChain:
    """Ordered list of provider fallbacks."""
    primary: ProviderConfig
    fallbacks: List[ProviderConfig]
    fallback_on_timeout: bool = True
    auto_retry_cooldown: float = 300.0
```

## 6. Retry/Backoff/Cooldown 当前策略

```
retry_backoff: exponential
  - attempt 1: 5s
  - attempt 2: 10s (5*2)
  - attempt 3: 20s (10*2)
  - total max wait with jitter: ~45s
  - canary_timeout: 45s
  - health_check_cooldown: 120s
```

v1.3 改进:
- 增加 jitter window 配置
- cooldown 可配置（当前 120s 硬编码）
- 失败记录保留时间可配置

## 7. 只读本地命令不受影响 (维持不变)

以下命令永远不依赖 provider canary:
- `inspect`, `dashboard`, `shell`, `shell-from-loop`
- `agent-state`, `agent-state-from-loop`
- `modules`, `task-cards`, `readiness`
- `pr-pack`, `pr-comment` (local only)
- `live-events`, `live-events-from-loop`
- `live-dashboard`, `live-dashboard-from-loop`
- `live-server`
- `monitor`, `monitor-loop`
- **`provider-status`** (本身显示状态)
- `export-task-card`, `preview`
- `evidence`, `repair-cards`, `from-loop`
