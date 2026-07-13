# Plan Review Checklist

계획 작성 완료 후 저장 전에 확인한다.

| 항목 | 확인 |
|------|------|
| 모든 Task에 정확한 파일 경로가 있는가 | |
| 모든 Step이 실행 가능한 구체적 행동인가 | |
| 검증 명령어와 예상 출력이 있는가 | |
| 스펙의 모든 요구사항이 포함되었는가 | |
| **한국어 우선 작성**: 새 계획 문서의 제목, 상단 요약, 진행 표, 사용자 결과 표, Task/Milestone 설명이 한국어를 기본값으로 쓰는가 | |
| **사용자 결과**: 사용자가 얻는 최종 사용자 결과가 상단에 한 문장으로 있는가 | |
| **진행 스냅샷**: 진행 요약이 완료됨/현재 위치/다음 단계/완료 신호로 간단히 드러나는가 | |
| **사용자 결과 요약**: 사용자가 받을 결과, 대상 사용자, 일상 사용 변화, 바뀌지 않는 경계를 기술 작업보다 먼저 설명하는가 | |
| **사용자 진행 계획**: milestone마다 사용자에게 보이는 결과, implementation owner surface, verification이 연결되는가 | |
| **사용자에게 보이는 마일스톤**: 각 Task가 사용자에게 보이는 변화와 연결되는가 | |
| **Term Clarity / 용어 명확성**: 사용자 언어를 기술 용어보다 먼저 쓰고, 다음 행동·완료 판단·안전·복구에 필요한 전문용어는 첫 사용 시 설명하는가. 이 경계에 걸리지 않는 표현 문제는 비차단 wording suggestion으로 다루는가 | |
| **Prompt Boundary**: reader-first 섹션이 presentation contract이며 approval/protected-path/reviewer authority/prompt hierarchy를 override하지 않는다고 명시하는가 | |
| Task 간 의존성이 올바른 순서로 정렬되었는가 | |
| **의존성 분석 / 의존성 게이트**: 기술 스택, 파일 구조, all planned `Run:` commands, runtime assumptions 기준으로 외부 의존성이 선언되었는가 | |
| 외부 의존성이 있으면 `preflight`, `fallback.available`, fallback verification, `failure_behavior`가 `writing-plans/SKILL.md` 계약과 일치하는가 | |
| **Document Readiness / DDL**: user-facing 변경이면 PRD vocabulary, docs/project co-update, RTM trace, route-specific empty-state 경계가 필요한지 확인했는가 | |
| **UI / Wireframe Evidence**: wireframe, visual parity, Browser QA 주장이 있으면 browser-level DOM, computed style, geometry/layout, screenshot artifact, interaction evidence를 요구하는가 | |
| **Selector Ownership**: classes/selectors/tokens 또는 legacy wrappers를 제거/대체하면 selector ownership, replacement owner, orphaned risk 검증이 있는가 | |
| **Summary-only Guard**: summary-only PASS, count, heading check만으로 UI/document readiness claim을 닫지 않는가 | |
| **Simplicity Gate**: 요구사항 이상의 과잉 설계가 없는가 (KISS/YAGNI) | |
| **MVP Focus**: 목표 달성을 위한 '가장 단순한 경로'인가 | |
| placeholder나 TODO가 남아있지 않은가 | |

**기준**: 이 계획만 보고 에이전트가 막힘 없이 실행할 수 있는가.

누락 시 리뷰어는 어떤 필드가 빠졌는지 구체적으로 적고, 사용자 결과 또는 진행 요약 문구의 수정 방향을 제안한다.
새 계획이 legacy English labels를 기본 표면으로 쓰면 한국어 우선 작성 위반으로 FAIL 처리한다. 기존 계획을 리뷰할 때는 legacy English labels를 읽을 수 있지만, 수정 범위에 들어온 계획은 한국어 섹션으로 보정한다.
`사용자 결과 요약` 또는 `사용자 진행 계획`이 없거나 너무 기술 용어 중심이면 FAIL로 처리한다.
사용자가 다음 행동, 완료 판단, 안전, 복구를 위해 이해해야 하는 unexplained specialist terms 또는 불필요한 전문용어에 의존하면 FAIL로 처리한다.
