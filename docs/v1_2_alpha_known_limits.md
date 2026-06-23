# v1.2-alpha Known Limits

## Provider Reliability

| Limit | Detail |
|-------|--------|
| **Provider status** | `degraded` |
| **Model** | `opencode-go/deepseek-v4-flash` |
| **Endpoint** | Reachable (DNS/TLS/HTTP OK) |
| **Inference** | Times out on minimal canary (`prompt="OK"`, `max_tokens=10`) |
| **Cause** | Upstream model inference timeout or SSE hang |
| **Impact** | 🔴 Long implementation phases requiring model calls will fail |
| **Impact** | ✅ **Does not block** any local readonly feature (dashboard, shell, monitor, live events, agent state, PR pack) |
| **Mitigation** | Run `harness copilot provider-status` before long phases; use `check_before_long_phase()` in Phase scripts |
| **Retry policy** | `max_retries=3`, exponential backoff with jitter, `read_timeout=90s`, `canary_timeout=45s` |

## Platform

| Limit | Detail |
|-------|--------|
| **Windows native** | Not sealed; WSL2 is recommended for Windows use |
| **macOS** | Not tested in this seal cycle; Python dependencies may vary |
| **Distribution** | No pip/pipx package published; run from source checkout only |

## API Integration

| Limit | Detail |
|-------|--------|
| **GitHub API** | ❌ Not included in v1.2-alpha; `pr-pack` is local-only |
| **GitLab API** | ❌ Not included |
| **External CI/CD** | ❌ Not connected — no automatic push, deploy, or merge |
| **Cloud storage** | ❌ No sync; all state files are local (`~/.harness/runtime/`) |

## Security

| Limit | Detail |
|-------|--------|
| **Credential storage** | ❌ Not included — no tokens, passwords, or API keys managed |
| **Authentication** | ❌ Not included — all features are local and readonly |
| **RBAC / access control** | ❌ Not included |

## Features Not in Scope

| Limit | Detail |
|-------|--------|
| **Automatic code repair** | ❌ Not automated — repair cards are informational only |
| **Agent control / auto-spawn** | ❌ Harness orchestrator role is not replicated |
| **Music / audio generation** | ❌ Out of scope |
| **3D StarMap UI** | ❌ Postponed |
| **Enterprise audit log** | ❌ Postponed |
| **Multi-project workspace** | ❌ Single project per session |
| **LLM-based analyses** | ❌ All analyses are deterministic (rule-based); no model calls are made by the copilot itself |

## Test Coverage

| Limit | Detail |
|-------|--------|
| **Full test suite** | 723 passed, 1 skipped (waiting companion placeholder has no implementation yet) |
| **E2E smoke tests** | Manual; no automated E2E framework in v1.2-alpha |
| **Performance benchmarks** | Not collected |

## Decision Record

- Provider degraded does NOT block final seal. All local readonly features are fully functional.
- Phase 9 (remote API integration, agent orchestration loop) will need provider reliability resolved first.
- Windows WSL2 guidance is a soft recommendation; no blocking issue identified.
