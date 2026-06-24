
> **Note**: This translation is pending refresh. See [README.md](README.md) / [README.zh.md](README.zh.md) for v1.3 current status.

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--rc.2-blue?style=flat-square" alt="버전">
  <img src="https://img.shields.io/badge/TypeScript-6.0-blue?style=flat-square" alt="TypeScript">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="라이선스">
  <img src="https://img.shields.io/badge/tests-528%20passed-brightgreen?style=flat-square" alt="테스트">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<h1 align="center">Harness OS</h1>
<p align="center"><em>Codex‑first 프로젝트 운영체제 — 통제 가능하고, 감사 가능하며, 재현 가능한 에이전트 엔지니어링</em></p>

---

**Harness OS**는 AI 코딩 에이전트를 위한 운영체제입니다. 프레임워크가 에이전트에게 *능력*을 주는 반면, Harness OS는 *경계와 규율*을 제공합니다. 모든 도구 호출은 게이트를 통과하고, 모든 출력은 마스킹되며, 모든 결정은 추적되고, 모든 전달은 검증됩니다.

이는 **AI 에이전트를 위한 Kubernetes**라고 생각하면 됩니다 — 컨테이너를 실행하기 위한 것이 아니라, 거버넌스, 관측 가능성, 감사 기능이 내장된 에이전틱 워크플로우를 실행하기 위한 것입니다.

---

## 왜 Harness OS인가?

LangChain, Vercel AI SDK, OpenAI Agents SDK 같은 프레임워크는 에이전트에게 도구 호출, 모델 사용, 워크플로우 구성 능력을 제공합니다. 하지만 다음 질문에는 답하지 못합니다:

- **누가 이 도구 호출을 승인했는가?** → Harness OS는 세션, 턴, 에이전트 ID로 모든 호출을 추적합니다.
- **출력에 비밀이 유출되었는가?** → Harness OS는 15개 이상의 비밀 패턴을 모든 출력 경계에서 자동 마스킹합니다.
- **무슨 일이 일어났는지 재생할 수 있는가?** → 모든 실행은 이벤트, 승인, 체크포인트를 포함한 구조화된 추적으로 기록됩니다.
- **전달이 안전한가?** → commit, PR, deploy 전에 암호화 무결성 해시로 검증이 통과해야 합니다.
- **정책을 강제할 수 있는가?** → 불변 필드, 단방향 안전 강화 규칙, fail‑closed 기본값을 갖춘 다계층 구성.

Harness OS는 **프레임워크가 아닙니다**. 모든 에이전트 런타임을 감싸서 프로덕션 환경에 대비시키는 **거버넌스 레이어**입니다.

---

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                   CLI (harness)                      │
│  create │ open │ init │ run │ verify │ deliver        │
│  config │ status │ report │ checkpoint │ rollback     │
│  skills │ decision │ repair │ check                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Turn Orchestrator                     │
│  Session → Input → Model Call → Tool Gate → Response │
└──────┬─────────┬──────────┬──────────┬─────────────┘
       │         │          │          │
┌──────▼──┐ ┌───▼────┐ ┌──▼────┐ ┌──▼──────────┐
│ Policy  │ │Approval│ │Secret │ │Observability │
│ Engine  │ │ Gate   │ │Redact │ │ Trace/Events │
└─────────┘ └────────┘ └───────┘ └──────────────┘
       │         │          │          │
┌──────▼─────────▼──────────▼──────────▼──────────┐
│            Verification & Delivery                │
│  Guard → Commit → PR → Release → Deploy          │
└──────────────────────────────────────────────────┘
```

### Thin Harness (구현 완료)

모든 에이전트 액션을 통제하는 최소 실행 가능 루프:

1. 턴 입력 수신
2. 모델 호출 실행
3. 도구 제안 생성
4. **PreToolUse 게이트** — 정책 평가 + 비밀 스캔
5. **Allow / Deny / NeedsApproval** 결정
6. **승인 해결** (필요한 경우)
7. 도구 실행
8. **PostToolUse 추적** — 모든 것 기록
9. 마스킹 처리된 최종 응답

### Thick Harness (계획 중)

프로덕션 규모 배포를 위한 확장 기능:
- 병렬 Hook 팬아웃 (발행‑수집 패턴)
- OpenTelemetry 통합
- 재시작 없는 정책 핫 리로드
- 다중 Provider 장애 조치 (Claude ↔ GPT ↔ 기타)
- 예산 기반 Provider 라우팅
- 분산 승인 UI
- 샌드박스 도구 실행

---

## 빠른 시작

### 사전 요구사항

- [Node.js](https://nodejs.org/) >= 22
- [pnpm](https://pnpm.io/) >= 11

### 설치 및 빌드

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd Harness-OS
pnpm install
pnpm build
```

### 실행

```bash
# 버전 표시
pnpm harness --version
# → 1.0.0-rc.2

# 도움말 표시
pnpm harness --help

# 설정 표시
pnpm harness config

# 설정 표시 (JSON)
pnpm harness config --json

# 사용 가능한 스킬 목록
pnpm harness skills list

# AGENTS.md 유효성 검사
pnpm harness check

# 프로젝트에 Harness OS 초기화
pnpm harness init --json

# 태스크 실행
pnpm harness run "인증 모듈에 테스트 추가"
```

### 일반적인 워크플로우

```bash
# 1. 프로젝트 초기화
cd my-project
harness init

# 2. 태스크 실행
harness run "사용자 인증 구현"

# 3. 검증 실행
harness verify

# 4. 전달 준비
harness deliver --commit --ver-id <검증ID>
```

---

## CLI 명령어

| 명령어 | 설명 |
|---|---|
| `create <name>` | 새 Harness OS 프로젝트 생성 |
| `open <path>` | 기존 프로젝트 열기 |
| `init` | 기존 프로젝트에 Harness OS 초기화 |
| `repair` | 누락되거나 유효하지 않은 프로젝트 구조 복구 |
| `check` | AGENTS.md 유효성 검사 |
| `status` | 현재 프로젝트 상태 표시 |
| `run <task>` | 태스크 실행 (전체 파이프라인) |
| `resume <run-id>` | 일시 중지되거나 중단된 실행 재개 |
| `verify` | 검증 파이프라인 실행 (lint, 타입검사, 테스트, 빌드) |
| `report <run-id>` | 실행 보고서 표시 |
| `deliver` | 전달 준비 (commit / PR / release / deploy) |
| `decision` | 아키텍처 결정 관리 (ADR) |
| `skills` | 스킬 관리 및 목록 표시 |
| `checkpoint` | git 및 태스크 상태를 저장하는 체크포인트 생성 |
| `rollback <checkpoint-id>` | 롤백 정보 표시 |
| `config` | Harness OS 설정 표시 |

모든 명령어는 `--json` (기계 판독 가능 출력)과 `--quiet` (최소 출력)을 지원합니다.

---

## 내장 기능

### 거버넌스 및 보안
- **권한 삼상태**: `allow` | `deny` | `needs_approval` — 모호한 상태 없음
- **비밀 마스킹**: 15개 이상의 패턴 — API 키, 토큰, 개인 키를 모든 출력에서 자동 마스킹
- **파일 보호**: 위험한 경로에 에이전트 접근 차단
- **안전 필드**: 불변 설정 필드, 단방향 약화 방지, 유니온 병합 배열
- **Fail‑closed**: 모든 Hook 실패는 기본적으로 `needs_approval`

### 검증
- `AGENTS.md`와 `package.json`에서 프로젝트 명령어 자동 감지
- 전체 파이프라인 실행: lint → 타입검사 → 테스트 → 빌드
- 암호화 무결성 해시가 포함된 구조화된 JSON 결과 생성
- 프로젝트, 태스크, 실행, git commit에 바인딩되어 부인 방지 제공

### 전달 파이프라인
- 가드 검사: 검증 바인딩, git 상태, 프로젝트 무결성
- 규약 기반 커밋 메시지 생성
- PR 본문 생성
- 완전한 감사 추적이 포함된 전달 보고서

### 관측 가능성
- **이벤트**: 세션, 행위자, 마스킹이 포함된 JSONL 이벤트 로그
- **추적**: 도구 호출, 컨텍스트 팩, 체크포인트를 포함한 전체 실행 추적
- **보고서**: 검증 결과가 포함된 Markdown 실행 보고서

### 스킬 레지스트리
위험 분류 및 승인 요구사항에 따른 내장 스킬:

| 스킬 | 위험 | 도구 |
|---|---|---|
| Filesystem | 중 | 읽기, 쓰기, 목록, 검색, 삭제 |
| Shell | 높음 | 명령어 실행, 테스트, 빌드 |
| Git | 중 | 상태, 차이, 커밋, 푸시 |
| Repo Scanner | 낮음 | 스캔, 감지, 매핑 |

---

## 프로젝트 구조

```
Harness-OS/
├── src/
│   ├── cli/              # CLI 진입점 + 포맷터
│   ├── config/           # 계층형 설정 로더 (안전 인식)
│   ├── governance/       # 정책 엔진, 마스커, Hook 프레임워크
│   ├── project/          # 프로젝트 라이프사이클 (생성/열기/초기화/복구)
│   ├── task/             # 태스크 라이프사이클 (생성/완료/실패)
│   ├── decision/         # ADR 관리 (제안/승인/거절)
│   ├── verification/     # 검증 파이프라인 + 결과 바인딩
│   ├── delivery/         # 전달 파이프라인 (가드/커밋/PR/보고서)
│   ├── observability/    # 이벤트, 추적, 실행 보고서
│   ├── runtime/          # 세션, 파이프라인, 턴 오케스트레이터
│   ├── context/          # 컨텍스트 팩 구축
│   ├── skills/           # MCP 스킬 레지스트리
│   └── state/            # 실행, 체크포인트, SQLite 상태
├── tests/
│   ├── unit/             # 528 단위 테스트
│   └── integration/      # 28 통합 테스트
├── harness_os_docs/      # 전체 설계 명세 (12개 문서)
├── .claude/              # Claude Code 프로젝트 설정
└── .project/             # Harness OS 로컬 상태 (gitignore)
```

---

## 문서

전체 설계 및 엔지니어링 명세는 [`harness_os_docs/`](harness_os_docs/README.md)에 있습니다:

| 문서 | 설명 |
|---|---|
| [01_ARCHITECTURE](harness_os_docs/01_ARCHITECTURE.md) | 시스템 아키텍처 및 핵심 원칙 |
| [02_CODEX_DEVELOPMENT_SPEC](harness_os_docs/02_CODEX_DEVELOPMENT_SPEC.md) | Codex 개발 명세 |
| [03_AGENTS_MD_STANDARD](harness_os_docs/03_AGENTS_MD_STANDARD.md) | AGENTS.md 프로토콜 표준 |
| [04_HARNESS_OS_DESIGN](harness_os_docs/04_HARNESS_OS_DESIGN.md) | 상세 시스템 설계 |
| [05_CONTEXT_ENGINEERING](harness_os_docs/05_CONTEXT_ENGINEERING.md) | 컨텍스트 엔지니어링 명세 |
| [06_TASK_DECISION_PROJECT_MANAGER](harness_os_docs/06_TASK_DECISION_PROJECT_MANAGER.md) | 태스크, 결정, 프로젝트 관리 |
| [07_MCP_SKILLS_SPEC](harness_os_docs/07_MCP_SKILLS_SPEC.md) | MCP 스킬 명세 |
| [08_GOVERNANCE_SECURITY](harness_os_docs/08_GOVERNANCE_SECURITY.md) | 거버넌스 및 보안 규칙 |
| [09_VERIFICATION_OBSERVABILITY](harness_os_docs/09_VERIFICATION_OBSERVABILITY.md) | 검증 및 관측 가능성 |
| [10_DELIVERY_PIPELINE](harness_os_docs/10_DELIVERY_PIPELINE.md) | 전달 파이프라인 명세 |
| [11_ACCEPTANCE_CRITERIA](harness_os_docs/11_ACCEPTANCE_CRITERIA.md) | 최종 승인 기준 |
| [12_OPEN_SOURCE_REFERENCES](harness_os_docs/12_OPEN_SOURCE_REFERENCES.md) | 오픈소스 참조 매핑 |
| [13_TESTING_STRATEGY](harness_os_docs/13_TESTING_STRATEGY.md) | 테스트 전략 |
| [14_ERROR_CODES](harness_os_docs/14_ERROR_CODES.md) | 에러 코드 참조 |
| [15_CONFIG_REFERENCE](harness_os_docs/15_CONFIG_REFERENCE.md) | 설정 참조 |
| [16_CLI_OUTPUT_CONTRACT](harness_os_docs/16_CLI_OUTPUT_CONTRACT.md) | CLI 출력 계약 |
| [17_PROJECT_STORAGE_GIT_POLICY](harness_os_docs/17_PROJECT_STORAGE_GIT_POLICY.md) | Git 및 저장소 정책 |
| [18_MIGRATION_VERSIONING](harness_os_docs/18_MIGRATION_VERSIONING.md) | 마이그레이션 및 버저닝 |

---

## 개발

```bash
# 타입 검사
pnpm typecheck

# 단위 테스트 실행
pnpm test:unit

# 통합 테스트 실행
pnpm test:integration

# 전체 테스트 실행
pnpm test

# 커버리지 테스트 실행
pnpm test:coverage

# 빌드
pnpm build

# 코드 포맷
pnpm format
```

### 테스트 현황

- **528개 단위 테스트** — 19개 테스트 파일, 모두 통과
- **28개 통합 테스트** — 1개 테스트 파일, 모두 통과
- **커버리지 임계값**: 80% (vitest.config.ts에서 설정)
- **TypeScript**: 엄격 모드, `src/`에서 `as any` 완전 제거

---

## 설계 원칙

1. **경계 명확성**: 각 모듈은 명확한 책임을 가집니다. 갓 객체(god object)는 없습니다.
2. **보수적 권한**: 기본값은 `needs_approval`입니다. 절대 `allow`를 기본값으로 하지 않습니다.
3. **상태 추적 가능성**: 모든 쓰기에는 스키마, 범위, 행위자, 이유, 추적 ID가 있습니다.
4. **도구 호출 감사 가능성**: 모든 호출은 누가, 무엇을, 입력, 결정, 타임스탬프를 기록합니다.
5. **낮은 결합도**: Thin Harness 우선. Thick Harness는 확장으로서 절대 혼합하지 않습니다.
6. **Fail‑closed**: Hook 실패, 타임아웃, 파싱 불가능한 결과 → `needs_approval`.

---

## 상태

**v1.0.0-rc.2** — 핵심 거버넌스 및 검증을 위한 릴리스 후보.

구현 완료:
- ✅ CLI 프레임워크 (17개 명령어)
- ✅ 다계층 설정 + 안전 필드 강제
- ✅ 비밀 마스킹 (15개 이상 패턴, 모든 출력 경계 커버)
- ✅ 무결성 바인딩이 있는 검증 파이프라인
- ✅ 가드 검사가 있는 전달 파이프라인
- ✅ 관측 가능성 (이벤트, 추적, 실행 보고서)
- ✅ ADR 관리 (제안/승인/거절/대체)
- ✅ 세션 및 상태 관리
- ✅ 태스크 라이프사이클 (생성 → 실행 → 완료 → 보고서)
- ✅ 스킬 레지스트리 (4개의 내장 스킬)
- ✅ 체크포인트 및 롤백 분석
- ✅ 528개 단위 테스트 + 28개 통합 테스트

v1.1+ 계획:
- 정책 핫 리로드
- 다중 Provider 런타임 (Claude + GPT + 오픈 모델)
- 분산 승인 UI
- OpenTelemetry 내보내기
- 샌드박스 도구 실행

---

## 라이선스

ISC
