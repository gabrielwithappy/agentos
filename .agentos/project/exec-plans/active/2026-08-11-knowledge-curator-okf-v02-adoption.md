# Knowledge Curator OKF v0.2 적용 구현 계획

> **상태:** 구현 계획 (리뷰 대기)
> **작성일:** 2026-08-11
> reviewed: false
> **usability_review_required:** true
> user_request: `catalog/skills/knowledge-curator`와 `/home/gabriel/agent/prj-agent/agentos-workspace/references/okf`의 구현을 비교하여 적용 가능한 기능을 분석하고, 구현 계획 문서만 작성한다.
> active_agent: Codex
> active_session: /home/gabriel/agent/prj-agent/agentos-workspace/agentos (branch: plan/okf-adoption-comparison)
> dashboard_item_id: PVTI_lAHOBiJEFc4Bek_Ezg1-qdo<br>
> implementation_completed_at:
> implementation_duration:
> implementation_baseline_commit:
> implementation_preexisting_status:

> **에이전트 작업자용:** 단계 추적에는 체크박스(`- [ ]`) 문법을 사용한다. 다음 단계로 진행하기 전에 각 단계를 완료한다.

**목표:** 현재 독립형 `knowledge-curator`에 OKF v0.2 starter bundle 생성과 결정적 읽기 전용 적합성 검사를 추가하되, 로컬 Git 백업 전용·무의존성 runtime 경계를 유지한다.

**사용자 결과 요약:** 사용자는 빈 knowledge checkout을 OKF의 `index.md`·`log.md`와 최소 concept 예제를 갖춘 번들로 명시적으로 초기화하고, 작성한 Markdown 번들이 필수 `type`과 기본 구조를 충족하는지 네트워크·원격 쓰기·자동 수정 없이 검사할 수 있다. 이 계획은 그래프 UI, 자동 hook, 원격 CI, MCP/임베딩 검색을 추가하지 않는다.

**의존성 분석:**
- 외부 의존성: 없음.
- 스캔 기준: 구현은 Python 3 표준 라이브러리, Git, Bash, pytest만 사용한다. 참조 구현의 `uv`/PyYAML, GitHub Actions, 브라우저, Claude Stop hook, MCP server, Node/pnpm 및 LLM provider는 이번 계획의 명령·runtime assumption에 포함하지 않는다.

**장기 적용 표면:**
- Traceability Surface: 이 active plan, 선행 standalone plan, `HISTORY.md`, lifecycle board, Gate 2 review artifacts.
- Durable Result Surface: `catalog/skills/knowledge-curator/`의 CLI·validator·사용자 지침과 focused regression tests.
- documentation-only exception: 없음. 이 문서는 구현 승인을 위한 계획이며 실행 결과가 아니다.

**진행 상태:** 참조 구현 비교와 후보 선별을 완료했고, 계획 Gate 2 리뷰 대기 중이다.

**아키텍처:** `knowledge_core.py`가 checkout 생성·경계 검사를 소유하고, `knowledge.py`는 argparse adapter로만 남긴다. 새 `okf_bundle_validate.py`는 네트워크 접근·Git 실행·파일 수정을 하지 않는 별도 checker이며, starter 작성과 validator 결과를 공통 JSON line/exit-code 계약으로 노출한다. AgentOS adapter와 AHA bridge는 바꾸지 않는다.

**기술 스택:** Python 3.11 표준 라이브러리, Git CLI, Markdown/YAML-frontmatter의 최소 텍스트 파싱, JSON line, pytest, Bash.

---

## 진행 스냅샷

| 필드 | 현재 값 |
|---|---|
| 전체 상태 | 리뷰 대기 |
| 완료됨 | 두 구현 및 참조 하위 프로젝트의 기능·경계 비교, 적용/제외 후보 선별, 계획 초안 작성 |
| 현재 위치 | Gate 2 리뷰와 사용자 승인 대기 |
| 다음 단계 | 선행 standalone plan 완료·검증 확인 후 Task 0부터 실행 |
| 완료 신호 | starter bundle·읽기 전용 OKF 검사·안전 경계 regression이 모두 PASS |

## 사용자 진행 계획

| 마일스톤 | 사용자에게 보이는 결과 | 구현 소유 surface | 검증 |
|---|---|---|---|
| 1. 실행 기준선 | 기존 독립 skill이 먼저 안정화되어 기능 소유권 충돌이 없음 | 선행 plan 및 `catalog/skills/knowledge-curator/` | `Run:` focused standalone suite / `Expected:` PASS |
| 2. OKF starter | 새 checkout에 안전한 최소 OKF 번들을 명시적으로 생성 | `knowledge_core.py`, `knowledge.py`, `SKILL.md` | `Run:` starter test / `Expected:` PASS |
| 3. 적합성 검사 | 사용자 작성 번들의 구조 오류를 수정 없이 확인 | `okf_bundle_validate.py`, tests | `Run:` validation suite / `Expected:` PASS |
| 4. 경계 고정 | 원격 쓰기·인플레이스 migration·UI/runtime 확장이 없음을 검증 | focused tests, docs | `Run:` boundary suite / `Expected:` PASS |

## 비교 분석 및 적용 결정

| 참조 구현 / 기능 | 현재 knowledge-curator 상태 | 결정 | 근거와 계획 반영 |
|---|---|---|---|
| `okf-skills`: one concept = one Markdown, `index.md` progressive disclosure, `log.md` | Git checkout만 초기화하며 OKF 번들 skeleton은 없음 | 적용 | `init --okf-starter` opt-in으로 starter를 생성한다. 기존 `init`의 빈 checkout 기본값은 바꾸지 않는다. |
| `okf-skills`: deterministic v0.2 checker, JSON·strict warning gate | `okf_bundle_validate.py`는 stub이며 skill runtime은 stdlib-only | 부분 적용 | 필수 structural contract(`index.md`, `log.md`, parseable frontmatter, non-empty `type`, root version)를 읽기 전용으로 검사한다. optional v0.2 trust/provenance/lifecycle family는 warning으로 보고한다. |
| `okf-skills`: `--migrate` v0.1 → v0.2 in-place rewrite | 현재 no-overwrite/backup-first 안전 정책 | 제외 | 묵시적 또는 CLI-driven mutation은 별도 approval과 recovery 설계가 필요하다. 후속 독립 계획 없이는 추가하지 않는다. |
| `okf-skills`: self-contained graph visualization, browser sanitization | terminal/Git curator이며 HTML renderer 없음 | 제외 | 정적 UI·renderer·XSS boundary·새 dependency가 추가되어 현재 요청의 최소 범위를 넘는다. |
| `okf-skills`: GitHub Action 및 Stop hook upkeep | standalone package는 remote write·자동 hook을 거부 | 제외 | CI/hook installation과 자동 finish 차단은 운영 권한을 넓힌다. 별도 user request와 dependency gate가 필요하다. |
| `pi-llm-wiki`: source capture, guardrails, backlinks, MCP parity, embeddings/watch | curator는 portable local checkout 관리 도구 | 제외 | Node/MCP/LLM/live runtime과 index state를 도입해 단순한 durable Markdown·Git 목적을 벗어난다. |
| `lineage-skill`: course/apprenticeship graph, assessment/runtime state | 교육 도메인 기능 없음 | 제외 | knowledge curation과 다른 도메인 모델이며 사용자 요청의 적용 대상이 아니다. |

### 채택 계약

- `init --okf-starter`는 **새로 만든 빈** `docs/knowledge` checkout에서만 `index.md`, `log.md`, `concepts/getting-started.md`를 작성한다. populated path와 `--adopt-existing` 조합은 안전 거부한다.
- `init --okf-starter`는 모든 대상 부재·부모 directory write 가능 여부를 먼저 preflight하고, private temporary directory에서 세 파일을 완성한다. 기존 root에 세 파일을 설치하므로 multi-file atomic rename을 주장하지 않는다. 대신 `.git/knowledge-curator-starter-state.json`에 created path와 staged-content SHA-256을 기록한 뒤 no-overwrite per-file rename을 수행한다. ordinary write failure는 journal에 기록된 digest와 같은 이번 invocation 생성물만 remove하고 starter file 0개로 복구한다. process interruption으로 journal이 남으면 다음 invocation은 journal/digest를 검증해 일치하는 생성물만 cleanup하고, mismatch는 code `2` no-change `OKF_STARTER_RECOVERY_REQUIRED`로 중단한다.
- cleanup 뒤 re-entry는 real `docs/knowledge/.git` repository이고 top-level entry가 `.git`뿐이며 existing `origin`이 credential-safe supplied remote와 같고 current branch가 requested branch일 때만 허용한다. 이 경우 Git init/remote/branch mutation 없이 starter를 재시도한다. 그 외 populated/mismatch/non-repository 상태는 code `2` no-change다. write failure의 recovery는 `next: "Run status, correct filesystem permissions, then retry init --okf-starter with the same --remote and --branch."`이고 `changed: false`/exit `3`이다.
- `validate --project <path>`는 읽기 전용이다. stdout은 항상 JSON object **한 줄**이고 stderr는 비어 있다. envelope은 `{ok:boolean, code:0|2|3, action:"validate", changed:false, diagnostics:[{path,severity:"error"|"warning",code,message}], next:string}`이다. error/refusal은 exit `2`, unreadable/non-UTF-8/oversized(1 MiB 초과) file 또는 filesystem error는 exit `3`, error가 없으면 exit `0`이다.
- `validate --strict`를 적용한다. 기본 mode에서는 warnings가 있어도 exit `0`, strict mode에서는 warning이 하나 이상이면 exit `2`이고 files는 그대로다. `--migrate`는 명령으로 등록하지 않고 parser error(JSON error, exit `2`)로 거부한다.
- 검사 discovery 범위는 bundle root의 `index.md`, `log.md`, 그리고 reserved file을 제외한 하위 directory의 `*.md`만이다. symlink, binary/NUL, 1 MiB 초과 file은 traversal하지 않고 refusal diagnostic을 낸다. `index.md`/`log.md`는 concept가 아니므로 `type` 검사의 대상이 아니다.
- 허용 frontmatter grammar는 UTF-8 text의 첫 줄 `---`, closing `---`까지의 flat YAML subset뿐이다: `key: plain-or-single/double-quoted scalar`, `key:` 뒤에 같은 indent의 `- plain-or-quoted scalar` list. duplicate keys, tabs, block scalar, anchors/tags, flow collection, nested mapping/list, blank key 및 closing boundary 누락은 `OKF_FRONTMATTER_UNSUPPORTED` error다. `type`은 non-empty scalar여야 한다.
- required structural checks: bundle root 존재, `index.md`와 `log.md` 존재, `index.md`의 exact scalar `okf_version: 0.2`, 발견 concept의 valid frontmatter와 non-empty `type`.
- advisory checks: missing `description`, `status` not in `draft|stable|deprecated`, malformed `sources` scalar/list, malformed `generated`/`verified`/`stale_after`, legacy `timestamp`/`# Citations`는 warning이다. diagnostics는 path lexicographic → severity(error before warning) → code lexicographic 순으로 stable하게 정렬한다.
- advisory field grammar: `sources`는 non-empty plain/quoted scalar 또는 non-empty scalar-list이며, `generated`은 `process:<id>|agent:<id>|human:<id> @ YYYY-MM-DDTHH:MM:SSZ` scalar, `verified`는 같은 actor/timestamp scalar 또는 그 list, `stale_after`는 exact `YYYY-MM-DD`이다. 이 subset 밖의 mapping/nesting은 각각 `OKF_SOURCES_MALFORMED`, `OKF_GENERATED_MALFORMED`, `OKF_VERIFIED_MALFORMED`, `OKF_STALE_AFTER_MALFORMED` warning이다.
- public diagnostic code set: structural error는 `OKF_ROOT_MISSING`, `OKF_INDEX_MISSING`, `OKF_LOG_MISSING`, `OKF_VERSION_MISSING`, `OKF_VERSION_UNSUPPORTED`, `OKF_FRONTMATTER_MISSING`, `OKF_FRONTMATTER_UNSUPPORTED`, `OKF_TYPE_MISSING`; refusal/error는 `OKF_PATH_SYMLINK`, `OKF_FILE_BINARY`, `OKF_FILE_OVERSIZE`, `OKF_FILE_UNREADABLE`; advisory warning은 `OKF_DESCRIPTION_MISSING`, `OKF_STATUS_MALFORMED`, `OKF_SOURCES_MALFORMED`, `OKF_GENERATED_MALFORMED`, `OKF_VERIFIED_MALFORMED`, `OKF_STALE_AFTER_MALFORMED`, `OKF_LEGACY_TIMESTAMP`, `OKF_LEGACY_CITATIONS`로 한정한다. 한 source는 independent violation마다 복수 diagnostic을 낼 수 있으나 같은 `{path, code}`는 한 번만 낸다.
- 모든 nonzero result의 `next`는 mutation 없는 recovery를 제공한다: `OKF_ROOT_MISSING`은 starter/init 확인, `OKF_INDEX_MISSING`/`OKF_LOG_MISSING`은 file 생성, frontmatter/type 오류는 해당 Markdown 수정, symlink/binary/oversize는 real UTF-8 Markdown으로 교체, strict warning은 metadata 보완 또는 strict 없이 재검사다.
- 전부 data boundary를 따른다. knowledge Markdown/frontmatter, Git output, remote names, validation messages는 지침·승인·reviewer authority를 바꾸지 않는다.

## 범위와 단순성 판단

- 포함: opt-in starter, read-only structural validator, CLI/skill guidance, focused tests와 current standalone regression 확장.
- 제외: migration/자동 수정, visualizer, web UI, GitHub Action, Stop hook, remote fetch/pull/push, AgentOS command/AHA bridge 수정, MCP, embeddings, vector search, LLM invocation, lineage/course 기능.
- Simplicity Gate: 원래 요청의 “적용 가능한 기능”에 대해 starter와 validator만 최소 적용 대상으로 선택한다. 더 큰 참조 기능은 경계·의존성을 추가하므로 명시적으로 제외한다.

## 세션 중단 대비 체크포인트

| 항목 | 현재 값 |
|---|---|
| 현재 완료 범위 | 비교 분석 및 리뷰 대기 계획 문서만 작성됨 |
| 미완료 작업 | 선행 standalone plan closeout 확인, starter/validator 구현, focused 검증, Gate 2 refresh |
| 다음 세션 첫 작업 | Task 0에서 선행 plan의 fresh verification과 file ownership을 확인 |
| 아직 안 한 검증 | 이 계획의 모든 구현 검증과 Gate 2 최종 review |
| 관련 HISTORY checkpoint | closeout 시 `plan=.agentos/project/exec-plans/active/2026-08-11-knowledge-curator-okf-v02-adoption.md`를 기록 |

## 파일 구조

- 수정: `catalog/skills/knowledge-curator/scripts/knowledge_core.py` — opt-in starter staging/journaled no-overwrite install, JSON recovery contract.
- 수정: `catalog/skills/knowledge-curator/scripts/knowledge.py` — `init --okf-starter`, `validate`, `validate --strict`, JSON parser-error adapter.
- 수정: `catalog/skills/knowledge-curator/scripts/okf_bundle_validate.py` — stdlib-only, deterministic, read-only OKF structural checker.
- 수정: `catalog/skills/knowledge-curator/SKILL.md` — starter, validate/strict, no-overwrite/read-only recovery guidance.
- 생성: `tests/test_knowledge_okf_starter.py` — starter content, preflight, injected write failure, command help/recovery regression.
- 수정: `tests/test_okf_bundle_validation.py` — discovery, grammar, required/error, advisory/strict, JSON ordering/read-only/symlink/binary/size regression.
- 수정: `tests/test_knowledge_skill.py` — installed-copy CLI help, parser error, JSON/exit/next envelope regression.
- 수정: `tests/test_knowledge_git_security.py` — starter no-partial state and no Git/network invocation regression.
- 수정: `tests/harness/test_aha_knowledge_okf_validation.sh` — checker exit status를 숨기지 않는 direct-copy validation smoke. 파일이 아직 없으면 Task 2에서 생성한다.
- 참조만: `tests/test_knowledge_okf.py` — AgentOS managed-store contract는 수정하지 않는다. 해당 test가 새 standalone entrypoint 영향을 받으면 별도 reviewed follow-up plan으로 분리한다.
- 변경 금지: `agentos/knowledge/**`, `agentos/commands/knowledge.py`, `catalog/skills/knowledge-curator/scripts/aha_knowledge_bridge.py`, `.agents/**`, docs/project root files.

`SKILL.md`가 standalone package의 사용자 안내 owner이며 root project documents의 requirement·system authority를 바꾸지 않으므로 docs/project co-update는 범위 밖이다. 구현 중 그 authority/contract 변경이 필요해지면 현재 plan을 `NEEDS_CONTEXT`로 멈추고 별도 계획을 작성한다.

### Task 0: 선행 계획 및 변경 소유권 확인

**파일:** 이 active plan의 header `implementation_baseline_commit`, `implementation_preexisting_status`만 수정한다. source/test/skill 파일은 수정하지 않는다.

**사용자에게 보이는 마일스톤:** 이미 진행 중인 standalone skill 구현을 훼손하거나 중복 구현하지 않는 출발점이 확보된다.

- [ ] 선행 `2026-08-10-knowledge-curator-standalone-skill`의 header가 exact `완료`와 non-empty `implementation_completed_at`을 갖고 predecessor closeout의 `PASS knowledge-curator-final` evidence가 있으며, `catalog/skills/knowledge-curator/**`와 shared test/harness files에 staged·unstaged·untracked 변경이 없음을 확인한다. 검증이 끝나면 `git rev-parse HEAD` SHA와 allowlist 밖의 기존 `git status --porcelain --untracked-files=all` rows를 JSON-escaped 한 줄로 계산한다. 에이전트는 그 두 값만 `apply_patch`로 이 계획 header의 `implementation_baseline_commit`/`implementation_preexisting_status`에 기록한다. 하나라도 실패하면 이 계획은 `NEEDS_CONTEXT`로 중단하고 선행 계획을 먼저 마무리한다.

- [ ] header write 전에 SHA가 40 lowercase hex인지, status snapshot이 JSON string인지 local Python으로 검증하고, `apply_patch`의 exact old/new header line context를 사용한다. patch 후에는 Task 0 `Run:`의 read-only `grep`/JSON parse로 기록값을 재검증한다. shell substitution·`sed`·임의 text replacement로 plan을 수정하지 않는다.

Run: `grep -q '^> \*\*상태:\*\* 완료' .agentos/project/exec-plans/active/2026-08-10-knowledge-curator-standalone-skill.md && grep -q '^> implementation_completed_at: [0-9]' .agentos/project/exec-plans/active/2026-08-10-knowledge-curator-standalone-skill.md && grep -q 'PASS knowledge-curator-final' .agentos/project/exec-plans/active/2026-08-10-knowledge-curator-standalone-skill.md && git diff --quiet -- catalog/skills/knowledge-curator tests/test_knowledge_skill.py tests/test_knowledge_git_security.py tests/harness/test_aha_knowledge_standalone.sh tests/harness/test_aha_knowledge_git_workflow.sh tests/harness/test_aha_knowledge_security_boundary.sh tests/harness/test_aha_knowledge_okf_validation.sh && git diff --cached --quiet -- catalog/skills/knowledge-curator tests/test_knowledge_skill.py tests/test_knowledge_git_security.py tests/harness/test_aha_knowledge_standalone.sh tests/harness/test_aha_knowledge_git_workflow.sh tests/harness/test_aha_knowledge_security_boundary.sh tests/harness/test_aha_knowledge_okf_validation.sh && test -z "$(git status --porcelain --untracked-files=all -- catalog/skills/knowledge-curator tests/test_knowledge_skill.py tests/test_knowledge_git_security.py tests/harness/test_aha_knowledge_standalone.sh tests/harness/test_aha_knowledge_git_workflow.sh tests/harness/test_aha_knowledge_security_boundary.sh tests/harness/test_aha_knowledge_okf_validation.sh)" && python3 -m pytest tests/test_knowledge_skill.py tests/test_knowledge_git_security.py tests/test_knowledge_curator_evals.py -q && bash tests/harness/test_aha_knowledge_standalone.sh && bash tests/harness/test_aha_knowledge_security_boundary.sh && bash tests/harness/test_aha_knowledge_git_workflow.sh && python3 -c 'import json,re; p=".agentos/project/exec-plans/active/2026-08-11-knowledge-curator-okf-v02-adoption.md"; h=open(p).read(); base=next(x.split(": ",1)[1] for x in h.splitlines() if x.startswith("> implementation_baseline_commit: ")); prior=next(x.split(": ",1)[1] for x in h.splitlines() if x.startswith("> implementation_preexisting_status: ")); assert re.fullmatch(r"[0-9a-f]{40}",base); assert isinstance(json.loads(prior),str); print("PASS knowledge-curator-baseline-header")' && echo 'PASS knowledge-curator-baseline-ready'`

Expected: `PASS knowledge-curator-baseline-ready`

- [ ] 기존 `init`/`status`/`backup`/`sync` JSON exit contract와 no-push 경계를 snapshot test로 고정한다.

Run: `python3 -m pytest tests/test_knowledge_skill.py tests/test_knowledge_git_security.py -q && echo 'PASS knowledge-curator-existing-contract'`

Expected: `PASS knowledge-curator-existing-contract`

### Task 1: opt-in OKF starter bundle 생성

**파일:** 수정 `catalog/skills/knowledge-curator/scripts/knowledge_core.py`, `catalog/skills/knowledge-curator/scripts/knowledge.py`, `catalog/skills/knowledge-curator/SKILL.md`; 생성 `tests/test_knowledge_okf_starter.py`; 수정 `tests/test_knowledge_skill.py`, `tests/test_knowledge_git_security.py`.

**사용자에게 보이는 마일스톤:** 사용자는 hand-written boilerplate 없이도 최소 OKF v0.2 번들을 시작할 수 있고, 기존 빈 Git checkout 초기화는 그대로 쓸 수 있다.

- [ ] `knowledge.py init`에 `--okf-starter`를 추가하고, `knowledge_core.py`에 preflight, private staging, journaled no-overwrite install, injected-write-failure/crash recovery cleanup 및 narrow same-remote/branch re-entry를 구현한다. parser error도 JSON envelope/exit 2/`next`를 반환하고 `init --help`에는 opt-in/no-overwrite semantics가 나타난다.

Run: `python3 -m pytest tests/test_knowledge_okf_starter.py -q && echo 'PASS knowledge-curator-okf-starter'`

Expected: `PASS knowledge-curator-okf-starter`

- [ ] starter의 `index.md`에 `okf_version: 0.2`, title/description, progressive-disclosure 링크를, `log.md`에 ISO date 기록 형식을, example concept에 non-empty `type`을 작성한다. `--adopt-existing --okf-starter`와 populated checkout은 no-change error로 처리하고 write failure 후에는 starter file 0개와 `status` retry guidance를 검증한다.

Run: `python3 -m pytest tests/test_knowledge_okf_starter.py -k 'starter_contents or refuses_existing_or_adopted_checkout or write_failure_leaves_no_partial_bundle or retry_preserves_remote_branch_without_git_mutation or mismatch_refused' -q && echo 'PASS knowledge-curator-starter-safety'`

Expected: `PASS knowledge-curator-starter-safety`

- [ ] `SKILL.md`에 opt-in semantics, 생성 파일, no-overwrite recovery를 문서화한다.

Run: `python3 -m pytest tests/test_knowledge_okf_starter.py tests/test_knowledge_skill.py -k 'guidance or help or parser_error' -q && echo 'PASS knowledge-curator-starter-guidance'`

Expected: `PASS knowledge-curator-starter-guidance`

### Task 2: 읽기 전용 OKF v0.2 구조 검사

**파일:** 수정 `catalog/skills/knowledge-curator/scripts/okf_bundle_validate.py`, `catalog/skills/knowledge-curator/scripts/knowledge.py`; 수정 `tests/test_okf_bundle_validation.py`, `tests/test_knowledge_skill.py`, `tests/test_knowledge_git_security.py`; 생성 또는 수정 `tests/harness/test_aha_knowledge_okf_validation.sh`.

**사용자에게 보이는 마일스톤:** 사용자는 bundle을 바꾸지 않고 어떤 파일이 최소 OKF 구조를 위반하는지 JSON 진단으로 알 수 있다.

- [ ] `okf_bundle_validate.py`를 표준 라이브러리만으로 구현하고 `knowledge.py validate --project <path> [--strict]`에서 호출한다. checker는 채택 계약의 grammar/discovery/diagnostic ordering/envelope을 반환하며 shell, Git, network를 실행하지 않는다.

Run: `python3 -m pytest tests/test_okf_bundle_validation.py -q && echo 'PASS knowledge-curator-okf-validation'`

Expected: `PASS knowledge-curator-okf-validation`

- [ ] 필수 오류와 advisory warning을 분리하고 stable diagnostic code/order를 보장한다. valid/warning/default success/strict refusal/error/refusal의 stdout 한 줄, empty stderr, exit code, `changed:false`, `next`를 각각 fixture로 고정한다.

Run: `python3 -m pytest tests/test_okf_bundle_validation.py -k 'grammar or errors or warnings or strict or json_contract or diagnostic_order' -q && echo 'PASS knowledge-curator-okf-diagnostics'`

Expected: `PASS knowledge-curator-okf-diagnostics`

- [ ] validator 전후에 content hash가 같은지, symlink escape 및 binary/oversized input이 no-change rejection인지 regression으로 고정한다.

Run: `python3 -m pytest tests/test_okf_bundle_validation.py tests/test_knowledge_git_security.py -q && echo 'PASS knowledge-curator-okf-readonly-boundary'`

Expected: `PASS knowledge-curator-okf-readonly-boundary`

### Task 3: 사용자 안내와 전체 회귀 고정

**파일:** 수정 `catalog/skills/knowledge-curator/SKILL.md`, `tests/test_knowledge_okf_starter.py`, `tests/test_knowledge_skill.py`, `tests/test_knowledge_git_security.py`, `tests/test_okf_bundle_validation.py`, `tests/harness/test_aha_knowledge_okf_validation.sh`; Task 0에 기록한 plan header baseline만 참조한다.

**사용자에게 보이는 마일스톤:** 사용자는 safe local Git workflow 안에서 starter와 validation을 발견하고, 참조 구현의 제외된 기능이 임의로 활성화되지 않음을 확인할 수 있다.

- [ ] `SKILL.md`에 `init --okf-starter → validate [--strict] → backup`의 command transcript, populated/adopt refusal, warning/error/read-only recovery를 추가하고, migration·push·hook·visualize가 제공되지 않는다고 명시한다.

Run: `python3 -m pytest tests/test_knowledge_okf_starter.py tests/test_knowledge_skill.py -k 'guidance_contract or installed_help or parser_error_json' -q && echo 'PASS knowledge-curator-okf-guidance'`

Expected: `PASS knowledge-curator-okf-guidance`

- [ ] standalone direct-copy 실행과 모든 knowledge-curator focused suites를 실행한다. 테스트 fixture는 temporary local directories와 bare Git repository만 사용하며 user checkout/remote에는 쓰지 않는다.

Run: `python3 -m pytest tests/test_knowledge_skill.py tests/test_knowledge_git_security.py tests/test_knowledge_okf_starter.py tests/test_okf_bundle_validation.py -q && bash tests/harness/test_aha_knowledge_standalone.sh && bash tests/harness/test_aha_knowledge_security_boundary.sh && bash tests/harness/test_aha_knowledge_git_workflow.sh && bash tests/harness/test_aha_knowledge_okf_validation.sh && echo 'PASS knowledge-curator-okf-final'`

Expected: `PASS knowledge-curator-okf-final`

- [ ] source/CLI boundary와 excluded capability의 부재를 behavioral negative tests로 검사한다. Task 0 header의 exact `implementation_baseline_commit`과 `implementation_preexisting_status`를 읽고, checker는 tracked diff와 current staged/unstaged/untracked porcelain rows를 함께 비교한다. File Structure allowlist와 active plan path 밖의 current row는 preexisting snapshot에 exact하게 존재해야 한다. 따라서 Task 1–3의 new untracked 금지 파일도 FAIL이며, Task 0 이후의 active plan header update는 허용된다. `--push`, `--migrate`, visualization/MCP command와 Git `fetch|pull|push` invocation은 command-capture fixture에서 모두 거부·미호출이어야 한다.

Run: `python3 -m pytest tests/test_knowledge_git_security.py tests/test_knowledge_skill.py -k 'no_push_or_fetch_or_pull or rejects_migrate_or_visualize_or_mcp' -q && python3 -c 'import json,re,subprocess; p=".agentos/project/exec-plans/active/2026-08-11-knowledge-curator-okf-v02-adoption.md"; h=open(p).read(); base=next(x.split(": ",1)[1] for x in h.splitlines() if x.startswith("> implementation_baseline_commit: ")); prior=json.loads(next(x.split(": ",1)[1] for x in h.splitlines() if x.startswith("> implementation_preexisting_status: "))); allowed={p,"catalog/skills/knowledge-curator/SKILL.md","catalog/skills/knowledge-curator/scripts/knowledge_core.py","catalog/skills/knowledge-curator/scripts/knowledge.py","catalog/skills/knowledge-curator/scripts/okf_bundle_validate.py","tests/test_knowledge_okf_starter.py","tests/test_okf_bundle_validation.py","tests/test_knowledge_skill.py","tests/test_knowledge_git_security.py","tests/harness/test_aha_knowledge_okf_validation.sh"}; rows=subprocess.check_output(["git","status","--porcelain","--untracked-files=all"],text=True).splitlines(); committed=subprocess.check_output(["git","diff","--name-only",base,"HEAD"],text=True).splitlines(); bad_rows=[r for r in rows if r[3:] not in allowed and r not in prior.splitlines()]; bad_committed=[x for x in committed if x not in allowed]; assert re.fullmatch(r"[0-9a-f]{40}",base) and not bad_rows and not bad_committed, (bad_rows,bad_committed); print("PASS knowledge-curator-okf-scope-status")' && echo 'PASS knowledge-curator-okf-scope-boundary'`

Expected: `PASS knowledge-curator-okf-scope-boundary`

## 리뷰 반영 이력

- 초안: 참조 기능을 적용/부분 적용/제외로 구분하고, 선택된 기능만 Task 1–3에 연결했다.
- [Gate 2 1차] validator grammar/diagnostic/JSON/recovery, strict policy, starter atomicity, CLI help, exact file ownership, baseline/behavioral scope check, predecessor gate가 불명확함 → 채택 계약·파일 구조·Task 0–3에 결정적 규칙과 focused regression을 추가했다.
- [Gate 2 2차] multi-file atomicity·retry route, stable advisory grammar/code set, local baseline, Task별 file ownership, staged/untracked predecessor collision gate가 불완전함 → journaled recovery/re-entry, exact grammar/code, header baseline, Task-level ownership과 Git-state checks로 보완했다.

## 구현 결과

구현 후 작성: 실제 변경 경로, user-facing behavior, fresh verification 결과를 기록한다.

## 사용 방법

구현 후 작성: exact starter·validate commands와 warning/error recovery를 기록한다.

## 아카이브 결정

모든 구현과 fresh verification, Gate 2 재검토가 끝난 뒤에만 아카이브 여부와 근거를 기록한다.
