# Captain Code

> 감사 가능한 AI 코딩 워크플로.

![License](https://img.shields.io/badge/license-ISC-green?style=flat-square)
![Status](https://img.shields.io/badge/status-early%20development-orange?style=flat-square)
![Mode](https://img.shields.io/badge/mode-local--first-blue?style=flat-square)

[English](./README.md) · [中文](./README.zh.md) · [日本語](./README.ja.md) · **한국어**

---

## Captain Code란

Captain Code는 개발 작업을 **통제된 실행, 검토 가능한 증거, 게이트 결정, 반환 기록**으로 바꾸는 감사 가능한 AI 코딩 워크플로입니다.

개발자가 AI 코딩 agent의 원시 출력을 맹목적으로 신뢰하지 않고도 사용할 수 있도록 돕습니다. “agent가 완료했다고 말한다”를 그대로 받아들이는 대신, Captain Code는 모든 작업이 계약을 갖고, 모든 실행이 증거를 남기며, 게이트 결정이 수락하기 전까지는 어떤 결과도 신뢰 상태에 들어가지 않도록 요구합니다.

Captain Code는 **로컬 우선(local-first)**이며 읽기 우선입니다. 당신의 컴퓨터에서 당신의 저장소를 대상으로 동작하며, 스스로 push, 게시, 배포하지 않습니다.

## 해결하려는 문제

AI 코딩 agent는 diff와 자신감 있는 요약을 잘 만들지만, 그 작업이 올바르고 범위 안에 있으며 수락해도 안전하다는 것을 증명하는 데는 약합니다.

- agent의 주장은 증거가 아닙니다.
- 통과했다는 요약은 통과한 테스트가 아닙니다.
- “완료된 것처럼 보이는” diff는 안전하게 머지할 수 있는 diff와 같지 않습니다.

agent 주위에 워크플로가 없으면 검증되지 않은 출력을 신뢰하게 됩니다. Captain Code는 agent와 당신의 신뢰 상태 사이에 얇고 감사 가능한 계층을 두어, 수락이 분위기가 아니라 증거에 근거한 결정이 되게 합니다.

## 핵심 워크플로

```
TaskEnvelope → Invocation → Artifact / Evidence → Review → GateDecision → AuditEvent → ReturnRecord
```

| 객체           | 의미                                                          |
| -------------- | ----------------------------------------------------------- |
| `TaskEnvelope` | 작업 계약: 목표, 범위, 수락 기준, 제약.                      |
| `Invocation`   | 통제된 워크스페이스에 대한 한 번의 실행 시도.                |
| `Artifact`     | 산출물(diff, 생성 파일, 패치, 계획).                         |
| `Evidence`     | 판단을 뒷받침하는 근거(테스트 결과, 로그, 정책 점검).        |
| `Review`       | artifact와 evidence에 대한 평가: 승인, 수리, 차단.          |
| `GateDecision` | 흐름 결정: `PASS` / `REPAIR` / `BLOCK` / `ESCALATE`.        |
| `AuditEvent`   | 발생한 일에 대한 추가 전용(append-only) 기록. 추적성 목적.   |
| `ReturnRecord` | 상태 반환 기록: 무엇이 수락·거부되었거나 미해결로 남았는지.  |

이들은 **범용 프로토콜 객체**입니다. Captain Code는 이 프로토콜의 코딩 profile이지만, 객체는 재사용 가능하게 유지되며 코드 전용 용어로 좁혀지지 않습니다.

## 최소 예시

작업은 envelope로 시작합니다:

```yaml
# task_envelope.yaml
task_id: task-001
title: "Add a usage section to README"
user_request: "Document how to run the CLI in README.md"
scope:
  allowed_paths: ["README.md"]
  denied_commands: ["git push", "git merge"]
acceptance_criteria:
  - "README has a 'Usage' section"
test_commands: ["pnpm test"]
```

이후 워크플로가 실행됩니다:

1. **Invocation** —— worker는 메인 체크아웃이 아니라 통제된 워크스페이스(git worktree) 안에서 실행합니다.
2. **Artifact / Evidence** —— diff는 artifact로, 로그와 테스트 결과는 evidence로 기록됩니다.
3. **Review** —— 수락 기준에 비추어 artifact와 evidence를 평가합니다.
4. **GateDecision** —— `PASS`, `REPAIR`, `BLOCK` 또는 `ESCALATE`.
5. **AuditEvent** —— 모든 단계가 감사 로그에 추가됩니다.
6. **ReturnRecord** —— 무엇이 수락되었고 어떤 위험이 남았는지에 대한 최종 기록.

`GateDecision`이 수락하고 `ReturnRecord`가 기록되기 전까지는 아무것도 “완료”가 아닙니다.

## 현재 상태

Captain Code는 **초기이며 활발히 개발 중**이므로 그에 맞게 다뤄 주세요.

- **모드:** 로컬 우선, 읽기 우선 시맨틱 copilot.
- **현재 사용 가능:** 프로젝트 점검, diff 및 증거 수집, runner 루프(plan → execute → collect → review → gate), 보고서 생성.
- **강화 중:** 통제된 워크스페이스 실행과 마무리를 포함한 쓰기 측의 완전한 `TaskEnvelope → ReturnRecord` 루프.
- **샌드박스 주장 아님:** 통제된 워크스페이스는 git worktree입니다. 격리하는 것은 *변경*이지 호스트가 아닙니다. 보안 샌드박스가 **아닙니다**(안전 모델 참조).

> 명칭 안내: CLI는 현재 `harness` / `python -m harness.copilot.cli`로 호출되며, `captain-code` 명칭은 채택이 진행 중입니다. [docs/quickstart.md](./docs/quickstart.md)를 참조하세요.

## 안전 모델

Captain Code는 기본적으로 보수적입니다. 다음 규칙은 agent의 재량에 맡기지 않고 워크플로의 일부로 강제됩니다:

1. **`TaskEnvelope`가 없으면 worker를 실행하지 않는다.**
2. **`trace_id`가 없으면 신뢰된 실행이 없다.**
3. **diff 참조가 없으면 완료 상태가 없다.**
4. **테스트 결과가 없으면 완료 상태가 없다.**
5. **실패한 테스트는 수락될 수 없다.**
6. **범위를 벗어난 파일 변경은 격리되며**, 조용히 적용되지 않는다.
7. **코어 프로토콜 변경에는 사람의 승인이 필요하다.**
8. **세 번 연속 실패 시 일시 중지 또는 사람 검토가 발동된다.**
9. **`git push`, 게시, 배포는 차단된다.**
10. **`ReturnRecord`가 신뢰되기 전에 수락된 `GateDecision`이 있어야 한다.**

통제된 워크스페이스는 메인 체크아웃 오염을 방지하고 변경을 diff·삭제하기 쉽게 합니다. 다만 악의적인 명령이 로컬 파일, 환경 변수, 자격 증명을 읽는 것을 **막지는 못합니다**. 강한 격리(컨테이너, microVM)는 이 단계의 범위 밖입니다.

## Captain Code가 하지 않는 것

- “Agent OS”나 AI 운영체제가 **아닙니다**.
- 엔터프라이즈 거버넌스 플랫폼이 **아닙니다**.
- 당신의 AI 코딩 agent를 **대체하지 않습니다** —— 그 출력이 어떻게 수락되는지를 통제합니다.
- 로그인 상태를 **보관하지 않고**, API 키를 포함하지 **않습니다**.
- push, 게시, 배포를 **하지 않습니다**.
- 자신의 워크스페이스가 보안 샌드박스라고 **주장하지 않습니다**.

## 빠른 시작

설치와 첫 실행은 **[docs/quickstart.md](./docs/quickstart.md)**를 참조하세요.

쓰기 측 루프가 강화되는 동안 완전한 가이드형 빠른 시작은 아직 마무리 중입니다. 읽기 전용 점검 명령은 지금 사용할 수 있으며 어떤 저장소에서도 안전하게 실행됩니다.

## 문서

- [Quickstart](./docs/quickstart.md) —— 설치와 첫 실행
- [Workflow](./docs/workflow.md) —— 프로토콜 객체와 실행 루프
- [Architecture (lite)](./docs/architecture-lite.md) —— 구성 요소와 경계
- [Hermes loop lock](./docs/hermes-loop-lock.md) —— Hermes(State Machine Runner + Scheduler + Daily Reporter)의 runner 규칙과 안전 잠금

## 라이선스

ISC.
