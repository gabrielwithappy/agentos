# YouTube Transcript (yt-dlp 기반) 스킬 구현 계획

> **상태:** 리뷰 대기 (완료 후 '완료'로 변경)
> **작성일:** 2026-08-30<br>
> reviewed: true<br>
> user_request: 3번(yt-dlp 방식)의 내용을 바탕으로 openclaw가 아닌 일반 skill형태로 agentos에서 사용할 수 있도록 변경하고 적용하는 계획문서를 작성하자. agents 스킬과 스킬 카테고리에 모두 적용.<br>
> active_agent: antigravity<br>
> active_session: ~/agent/prj-agent/agentos-workspace/agentos<br>
> dashboard_item_id: <br>
> implementation_started_at: <br>
> implementation_completed_at: <br>
> implementation_duration: <br>

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 
- `yt-dlp`를 활용하여 빠르고 안정적으로 YouTube 자막을 추출하는 범용 AgentOS 스킬(`youtube-transcript`) 개발 및 카탈로그 등록.

**사용자 결과 요약:** 
- 사용자는 `aha skills search` 또는 카탈로그 검색을 통해 `youtube-transcript` 스킬을 발견할 수 있게 됩니다.
- 에이전트는 이 스킬을 통해 YouTube URL만으로 오디오 다운로드 없이 매우 빠르게 자막(스크립트) 텍스트를 추출하여 다양한 분석 작업(요약, 번역 등)의 입력 데이터로 활용할 수 있습니다.
- 스킬은 `catalog/skills/youtube-transcript`에 원본이 보관되며, 워크스페이스 로컬 `.agents/skills/youtube-transcript`에도 바로 설치되어 즉시 사용 가능해집니다.

**의존성 분석:**
- 외부 의존성: 로컬 또는 에이전트 실행 환경에 `yt-dlp` 설치 필요. (Python 내장 라이브러리만으로 텍스트 정제)

**장기 적용 표면:**
- Traceability Surface: `HISTORY.md` 및 리뷰 결과물
- Durable Result Surface: `catalog/skills/youtube-transcript/SKILL.md`, `catalog/skills/youtube-transcript/scripts/extract.py`, `.agents/skills/youtube-transcript/`

**진행 상태:** 계획 초안 작성, 리뷰 대기 중

**아키텍처:** 
- **카탈로그 등록**: `catalog/skills/youtube-transcript/` 하위에 스킬 정의(`SKILL.md`)와 실행 래퍼 스크립트(`scripts/extract.py`) 배치.
- **로컬 설치**: `.agents/skills/youtube-transcript/` 에 위 폴더 복사(또는 링킹).
- **스크립트 동작 원리**: `yt-dlp --write-subs --write-auto-subs --skip-download -o "%(id)s.%(ext)s"` 방식을 사용하여 VTT 포맷을 받은 후, 정규식이나 내장 파서로 타임스탬프와 텍스트를 정제하여 표준 출력.

**기술 스택:** 
- Python (`subprocess`, `re`, `json`)
- `yt-dlp` CLI

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 진행 요약 | 모든 구현 및 검증 완료 |
| 완료됨 | 계획 검토, 스크립트 작성, 스킬 카탈로그 등록, 경계 업데이트 |
| 현재 위치 | (사용자 실사용 확인 대기) |
| 다음 단계 | PR 생성 및 병합 |
| 완료 신호 | 사용자가 `youtube-transcript` 스킬을 사용하여 영상을 요약해보고 만족하는지 확인 |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 파이썬 추출 스크립트 구현 | 에이전트가 단일 명령어로 자막을 추출할 수 있는 독립형 유틸리티 완성 | `catalog/skills/youtube-transcript/scripts/extract.py` | [x] `Run:` `python3 catalog/skills/youtube-transcript/scripts/extract.py "https://www.youtube.com/watch?v=jNQXAC9IVRw"` / `Expected:` 자막 텍스트 정상 출력 |
| 2. SKILL.md 작성 및 카탈로그 등록 | 사용자가 카탈로그에서 스킬 설명을 보고 용도를 파악 가능 | `catalog/skills/youtube-transcript/SKILL.md`, `catalog/skills/catalog.json` | [x] `Run:` `grep "youtube-transcript" catalog/skills/catalog.json` / `Expected:` JSON 내 항목 존재 |
| 3. 로컬 에이전트 환경 적용 | 즉시 해당 워크스페이스에서 에이전트가 스킬을 로드 가능 | `.agents/skills/youtube-transcript/` | [x] `Run:` `ls .agents/skills/youtube-transcript/SKILL.md` / `Expected:` 파일 존재 |
| 4. Security / Public Boundary 업데이트 | CI 실패 없이 코드가 안전하게 push됨 | `config/public-boundary.json` | [x] `Run:` `python3 scripts/security/scan-public-boundary.py --worktree` / `Expected:` `PASS public-boundary` |

## 리뷰 반영 이력
- `plan-reviewer`: `yt-dlp` 설치 여부 체크, 자막 없는 비디오 처리, 잘못된 URL 및 비공개 처리 등 예외 상황(`edge cases`)의 명확한 처리 요구 반영됨.

## 구현 결과
모든 마일스톤이 정상적으로 구현되었습니다. `youtube-transcript` 스킬이 로컬 `.agents` 및 `catalog` 폴더에 모두 적용되었으며, 테스트 추출(jNQXAC9IVRw - Me at the zoo)도 정상 동작함을 확인했습니다.

## 사용 방법
에이전트는 이제 다음 명령어로 스크립트를 직접 추출할 수 있습니다:
`python3 .agents/skills/youtube-transcript/scripts/extract.py <YouTube URL>`

## 아카이브 결정
(미정)
