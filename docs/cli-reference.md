# AgentOS CLI Reference

AgentOS exposes one installed command, `agentos`, with `aos` kept as an alias.
The CLI stores user state under `AGENTOS_HOME` or `~/.agentos`.

## Commands

```bash
agentos [--version] [--help]
agentos run --once "Prompt" [--provider mock|codex|codex-cli|claude] [--json]  # sends one message and exits — stateless, no continuing session
agentos setup [--home PATH] [--path PROJECT_DIRECTORY]
agentos skill install SKILL_DIRECTORY
agentos skill status [--json]
agentos project init [--path PATH] [--json]  # runtime resources + starter project documents
agentos project status [--path PATH] [--json]
agentos gateway doctor [--provider PROVIDER] [--json]
agentos gateway submit --provider PROVIDER "Prompt" [--cwd PATH] [--record-policy metadata|full] [--json]
agentos gateway worker --once [--json]
agentos gateway list|status|events|cancel|retry|prune
agentos doctor [--json]
agentos session list
agentos session show SESSION_ID
agentos session resume SESSION_ID
agentos session delete SESSION_ID [--yes]
agentos session prune --before DATE [--yes]
agentos hook list
agentos hook enable NAME
agentos hook disable NAME
agentos hook config show
agentos hook bridge {codex|claude-code} {pre-bash|pre-write|post-bash|stop}
agentos llm status|login|logout --provider mock|codex|codex-cli|claude [--json]
agentos harness --project-root PATH [engine args...]
python -m agentos.runtime.bench --prompt "Prompt" [--provider mock|codex] [--format json] [--assert-warm-faster]
```

`agentos project init` creates `.agentos/project/` from the bundled starter
documents when that directory does not exist. Existing or partial project
documents are preserved; JSON output reports `project_documents.state` as
`current`, `partial`, or `not_initialized` and lists missing files.

## Gateway Core

Gateway Core is a managed local execution path for queued runs. It keeps state
under `AGENTOS_HOME/gateway/`, reuses the existing provider registry, and does
not replace direct vendor CLI usage.

See `docs/gateway-core.md` for `agentos gateway submit`, `agentos gateway worker --once`, retry, prune, and recovery details.

Running bare `agentos` starts an interactive session only when stdin and stdout
are TTYs. In pipes or redirects it exits with code `2` and points to
`agentos run --once "<prompt>"`.

## Canonical Session Runtime vs Stateless `--once`

`agentos` (bare, or `agentos run` without `--once`) is the canonical
interactive path: it starts a `ConversationRuntime`-owned session where every
turn's context (prior user/assistant/tool messages, in order) is actually
sent to the provider on the next turn, not just the newest prompt. This is
true for both the Textual TUI and its legacy interactive fallback (used only
when Textual itself fails to start) — both consume the same
`ConversationRuntime.submit_turn()` event stream, so context carries across
turns identically in either path.

`agentos run --once "Prompt"` is the deliberate opposite: **"Sends one message and exits; it does not continue an interactive session. Use agentos for a continuing conversation."** It uses the stateless
`stream_once(prompt)` compatibility shim — no prior turns, no provider
continuation, no session-runtime persistence. This is intentional: `--once`
exists for scripting/automation/one-shot JSONL output where a continuing
session would be the wrong tool. `agentos run --once --help` shows the same
guidance.

## AgentOS TUI

Bare `agentos` and `agentos run` open the AgentOS TUI in a real terminal. The
first screen shows `AgentOS`, a transcript, the composer placeholder
`Type a message or / for commands`, and a footer with `cwd`, `provider`,
`model`, `session`, `hooks`, `mode`, `last turn`, optionally `branch <name>`
(the current **git** branch; omitted when the working directory is not inside
a git repository or git is unavailable), optionally `convo-branch <id>:<label>`
(the active **conversation** branch — distinct from the git `branch` field
above; shown once a turn has run, and updated immediately after a fork or a
branch switch), and `total in/out N/M chars` (starts at `0/0` and accumulates
across turns in the session).

In the full-screen TUI, that detailed footer is compacted to one line using
`cwd:`, `pm:`, `sid:`, `git:`, `convo:`, `turn:`, `in:`, and `out:` labels.
On narrow terminals optional location and branch fields may be omitted and
values shortened with `…`; `turn`, provider/model, session, and usage remain.
Use `/status` whenever the complete, untruncated status is needed.

Type `/` or `/help` to show the command palette. The MVP commands are:

- `/help`
- `/login` — choose an LLM provider to sign in. With no argument, opens a provider selection prompt (codex / claude); press Esc to close the prompt without starting a login (you're returned to the composer, nothing changes). `/login codex` or `/login claude` skips the prompt and starts that provider's account-login flow directly. The flow attempts browser login first (default); if the browser cannot be opened, AgentOS falls back to device-code sign-in automatically within the same login flow (codex only — claude has no device-code fallback).
- `/status` — show the current TUI/session footer state and, when the active provider is `codex` or `claude`, append that provider's auth status and recovery guidance. On other providers (e.g. `mock`) it points you to `/login`.
- `/logout` — end the current account-login session for whichever provider is currently active (no forced switch to `codex`). If the session is already logged out, AgentOS reports that as a sanitized no-op success with guidance.
- `/hotkeys` — show all keyboard shortcuts in the transcript
- `/theme` — open a theme-picker modal; select a Textual built-in theme (21 available) to apply it immediately; `Esc` cancels without changing the theme; the choice is session-scoped and reverts to the default on restart
- `/session`
- `/session list`
- `/session resume`
- `/hooks`
- `/tools`
- `/usage`
- `/tree` — show the current session's turns as an indented tree with branch support.
- `/indicator` — switch loading indicator animation style (`ascii` | `unicode` | `emoji` | `kaomoji`).
- `/model` — switch the LLM provider for the current session (`mock` | `codex`).
- `/clear`
- `/exit`

`/tools` shows the tool calls from the last turn, or
`No tool calls in the last turn. Next: send a message that needs a tool.` if
none happened yet. `/usage` shows the last turn's input/output character
count, or `No usage yet. Next: send a message.` if no turn has completed yet.

Every ordinary conversation turn has an explicit request/result boundary that
does not depend on colour: the request is headed `You`, and the final result
is headed `AgentOS · responding`, then `AgentOS · complete`,
`AgentOS · cancelled`, or `AgentOS · failed`. The labels are presentation
only: copied text, persisted conversation messages, and forked turns retain
the original message body without a `You:` or `AgentOS` prefix.

In colour-capable terminals, the whole `You` request region also uses a subtle
background block so requests remain easy to locate while scrolling. AgentOS
answers and `Activity` entries keep their plain background (tool entries use
a theme-adaptive emphasis border). With `NO_COLOR=1` or a terminal that omits
background colours, the `You`/`AgentOS` headers above remain the role
distinction. `Activity` entries (reasoning and tool calls) keep a visible `│`
left boundary to separate multiple activity rows from each other.

Completed tool activity is collapsed by default: its row identifies the tool,
whether it completed or failed, and a sanitized result summary. Press `Ctrl+O`
to reveal or hide the sanitized call arguments and full result for every tool
activity in the current transcript. The same shortcut appears in `/hotkeys`.
Running tools remain visibly marked as running until a result arrives. This is
only a presentation choice: tool execution, approval, provider events, session
JSONL, `/tools`, and secret redaction behavior do not change.

While a turn is waiting for the first response chunk, the transcript shows a
`Thinking…` line. Pressing `Esc` at that point removes that indicator and
shows `Turn cancelled.`; the composer is already focused, ready for the next
message. If an answer has started, its partial body remains visible under
`AgentOS · cancelled`; it is not committed to conversation state. A completed
turn that contains no assistant text instead shows
`No response content was returned.` under `AgentOS · complete`.

Before the final answer, the transcript may show process entries describing
what the provider did before answering:

- `Activity · Thinking` — reasoning steps, displayed in a muted secondary
  region belonging to the current turn.
- `Activity · Tool · <name> · running|complete|failed` — a tool call and its
  result share one block. Completed blocks show a sanitized summary by default;
  `Ctrl+O` reveals the sanitized call and result in that same block. Some tools
  have a registered custom renderer for the result line; today the mock
  provider's `mock_tool` result renders as a `| field | value |` table.

Activity preserves provider event order and is not part of the final assistant
result; the final answer is rendered last.

### 답변 형식 (Response style)

AgentOS sends a fixed response-style instruction ahead of every request, so
answers lead with the conclusion and expand into implementation detail only
when asked. If an answer omits detail, it says so and invites a follow-up —
just ask "자세히 설명해줘" (or similar) to get the deeper explanation. One
thing this instruction never shortens: any action AgentOS actually took
(files changed, commands run) is always reported in full, regardless of how
brief the rest of the answer is.

Unknown commands show `Unknown command. Next: /help` and return focus to the
composer. `/session resume` opens the session-and-branch picker: with no
sessions it shows `No sessions found. Esc to return.`, with an unavailable
session it shows `Session unavailable. Next: /session list`, and — this is
the only place a session can be *statefully* resumed — if the resumed session
has more than one conversation branch (a prior fork), a second picker step
opens automatically (`Multiple branches found. Esc to keep the active branch.
Enter to switch.`) before the transcript is ready. `Esc` on the session
picker shows `Resume cancelled.`; `Esc` on the branch picker shows `Kept
active branch.` and keeps whichever branch was active when the session was
last saved.

The shell command `agentos session resume SESSION_ID` is **inspection-only**
— it prints the session's metadata and `Use agentos to resume a continuing
conversation.`; it never starts a turn, since a one-shot shell command exits
before any turn could run and cannot host a continuing conversation. Use the
TUI's `/session resume` picker (above) to actually resume one.

Keyboard behavior:

- `Ctrl-C` cancels an active turn and returns to the composer.
- `Esc` cancels a turn (shows `Turn cancelled.` and, after a first response
  chunk, marks its visible result `AgentOS · cancelled`), or closes overlays such as command or session
  picker views when no turn is waiting. An open overlay always takes
  priority, so `Esc` never cancels a turn while an overlay (for example the
  session resume picker) is on screen.
- `EOF` exits without a traceback or hang.
- `Shift+Enter` (`ShiftEnter` in grep-safe verification text) is reserved for newline input in the multiline composer.
- `Tab` moves focus out of the composer onto the most recent message in the
  transcript; further `Tab` presses step to older messages, `Shift+Tab` steps
  back toward newer ones, and focus wraps between the oldest message and the
  composer at either end. The focused message is shown with an accent border.
- `f`, pressed on a focused message, forks a new conversation branch from
  that message's turn immediately — the `convo-branch` footer indicator
  updates right away (not only after your next message), the fork shares the
  prior messages as an immutable prefix (nothing is copied or duplicated),
  and it never inherits the source branch's provider continuation, since the
  two branches can diverge from this point on. The fork is persisted right
  away too, so it survives even if you never send another message before
  closing AgentOS.
- `c`, pressed on a focused message, copies that message's full text to the
  system clipboard (via the terminal's OSC 52 escape sequence) and shows a
  "복사 시도됨" (copy attempted) notification. OSC 52 has no confirmation from
  the terminal, so this notification means the copy was sent, not guaranteed
  received — on terminals that do not support OSC 52 (for example macOS
  Terminal.app), nothing will actually land on the clipboard even though the
  notification appears.
- `/exit` exits the TUI cleanly.

When stdin or stdout is not a TTY, the TUI is not initialized. The command exits
`2`, stdout stays empty, and stderr contains
`Interactive mode requires a TTY. Next: agentos run --once "<prompt>".`

## Recovery Matrix

Every failure mode below produces a sanitized outcome plus an explicit next
action in both the TUI transcript and the JSONL event stream — never a raw
stack trace, provider stderr, token, or credential.

| Failure | Sanitized outcome shown | Next action |
| --- | --- | --- |
| Unauthenticated (Codex turn sent without sign-in) | `AgentOS-owned Codex sign-in is required.` | `Open another terminal and run: agentos llm login --provider codex` then `Then return here and run /status.` |
| Transport error (network/streaming failure) | The sanitized provider error message, e.g. `<message> Next: /status` | `Resend your message.` |
| Snapshot corruption (unreadable/malformed `.conversation-snapshot.json`) | Resume proceeds transparently via replay | The corrupted snapshot is discarded; state is rebuilt entirely from the durable `.conversation-events.jsonl` log — no crash, no data loss for already-committed turns |
| Replay across restart/resume | Prior turns' context is intact; no provider continuation is reused | A new process always starts a fresh transport-session epoch, so a persisted continuation handle from a previous run never matches and is never reused — the next turn falls back to full context replay automatically |
| Cancel (`Esc` while a turn is waiting) | `Turn cancelled.` | Composer is refocused; no partial user/assistant message, continuation, or branch head is committed — the conversation state is exactly as it was before the cancelled turn |

`/login`'s browser-first flow always shows `Open this URL to sign in:` followed
by the actual authorize URL — shown immediately, before AgentOS even attempts
to auto-launch a browser, since there is no way to know in advance whether
auto-launch will succeed (headless/remote/sandboxed sessions commonly can't
launch one at all). If the browser cannot be opened automatically, AgentOS
falls back to device-code sign-in in the same flow and shows a second hint,
`Could not open a browser automatically. Open <verification URL> and enter
code: <code>` (see [Native Codex Sign-In](#native-codex-sign-in---provider-codex)).
Both the TUI and the plain `agentos llm login` shell command show these
hints (the shell command writes them to stderr, keeping `--json` stdout as
exactly the final sanitized status payload).

## JSONL

`agentos run --once --json` writes one sanitized JSON object per stdout line.
Provider event names include `start`, `message_delta`, `reasoning`,
`tool_call`, `tool_result`, `done`, and `error`. `reasoning`/`tool_call`/
`tool_result` describe what the provider did before its final answer
(`message_delta`); consumers that only care about the final answer can ignore
unrecognized event types. CLI lifecycle metadata is added under
`metadata.cli`. Diagnostics and recovery text are written to stderr, not
JSONL stdout.

## Invocation Runtime Benchmark

Installed `agentos` is the canonical command path for everyday use. `uv run
agentos ...` is a development path that may include environment bootstrap
overhead and should not be used as the only evidence for user-perceived
runtime latency. The warm runtime measurement surface is available through:

```bash
uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --format json
```

The JSON output contains `uv_run`, `installed_cli`, `direct_provider`, and
`runtime_warm`, each with `bootstrap_ms`, `first_event_ms`, `provider_ms`,
`persistence_ms`, and `total_ms` phase timings. The current `codex` provider
still uses the external Codex CLI compatibility path; this benchmark does not
introduce native OAuth, native transport, credential parsing, or a daemon.

설치된 agentos가 없을 때:

```bash
bash scripts/verify-cli-isolated-install.sh
```

Expected: `PASS agentos-cli-isolated-install`. Until that passes, use
`uv run agentos ...` only as a development fallback.

runtime health check가 실패할 때:

```bash
uv run agentos doctor --json
```

Expected JSON fields include `launcher`, `runtime`, `recovery`, and
`next_action`. If `launcher.status` is `development_shim`, the `agentos`
found by that command is the active `uv`/virtualenv shim, not a shell-installed
canonical launcher. Follow `next_action`; if stale runtime cleanup is reported,
clean the stale runtime/socket state and rerun the benchmark before changing
architecture.

benchmark 결과가 기대보다 느릴 때:

```bash
uv run python -m agentos.runtime.bench --prompt "Reply with OK only." --provider codex --assert-warm-faster
```

Expected: `PASS invocation-runtime-benchmark` only when the measured warm path
beats the `uv run` path by at least the configured threshold and has lower
bootstrap time. Without that PASS line, do not start daemon/server-client
migration; keep the external CLI compatibility path and record the benchmark
evidence.

### Session Runtime Benchmark

Every provider declares an explicit capability (`ProviderCapabilities`,
`agentos/llm/types.py`): `context_aware=False` providers only support the
stateless `stream_once(prompt)` **compatibility fallback**, the same shim
`agentos run --once` uses — they are never silently selected for the
canonical multi-turn interactive path. Callers that need context-aware
invocation and get an unsupported provider receive a sanitized
`unsupported_capability` error with an explicit recovery action, not a
silent context drop or a stack trace.

```bash
uv run python -m agentos.runtime.bench --provider mock --runs 5 \
  --first-prompt "Remember AGENTOS_SESSION_MARKER=oak." \
  --second-prompt "What is AGENTOS_SESSION_MARKER?" \
  --assert-session-runtime
```

Runs one discarded warmup trial, then 5 paired two-turn trials alternating
continuation-reuse and forced-full-context-replay second turns, recording
`context_build_ms` (time to build the deterministic provider-bound context)
and `first_event_ms` for every sample. `PASS session-runtime-benchmark`
requires mock's `context_build_ms` p95 `<= 50ms` and the marker planted in
the first turn to survive into every second-turn response.

For the native `codex` provider, the same command requires explicit opt-in:

```bash
AGENTOS_CODEX_INTEGRATION=1 uv run python -m agentos.runtime.bench --provider codex --runs 5 \
  --first-prompt "Remember AGENTOS_SESSION_MARKER=oak." \
  --second-prompt "What is AGENTOS_SESSION_MARKER?" \
  --assert-session-runtime
```

Without `AGENTOS_CODEX_INTEGRATION=1` it prints `PASS
session-runtime-benchmark skipped=integration-disabled` and exits `0` — it
never silently runs against your real account. With the flag set, it runs an
authenticated preflight first; if unauthenticated it prints `STOP
session-runtime-benchmark unauthenticated` and exits `2`. Once opted in and
authenticated it never skips again: the outcome is always `PASS
session-runtime-benchmark` (context p95 within threshold, median second-turn
`first_event_ms` at least 250ms lower than an equivalent stateless
invocation, and the marker preserved across five linked turns) or a sanitized
`FAIL session-runtime-benchmark stop=daemon-follow-up-not-approved` — a
threshold failure never auto-proposes a daemon/client split.

## Bootstrap Context (`AGENTS.md`/`CLAUDE.md` and Skills)

Every brand-new session (never resumed/migrated from a prior session id)
automatically loads project context into its first trusted `system` message,
before any turn is submitted:

- **Project instructions**: AgentOS walks from the current working directory
  **up through every ancestor directory to the filesystem root**, looking for
  one `AGENTS.md` (or `AGENTS.MD`/`CLAUDE.md`/`CLAUDE.MD` as a fallback) per
  directory. This means a shared parent directory — a monorepo root, or even
  your home directory — can contribute a file you did not expect. A global
  `AGENTOS_HOME/core/AGENTS.md`/`CLAUDE.md` is also included if present. Review
  what ancestor directories exist above any project you run `agentos` from if
  this matters to you.
- **Installed skills**: name/description/location metadata for every skill
  under `AGENTOS_HOME/core/.agents/skills/` is listed — never the full skill
  body. When a task needs one, the `read` tool can load only that listed
  skill's `SKILL.md`; manifests, companion assets, and other global paths are
  not readable through the tool.

Unreadable files (permission error, bad encoding, broken symlink) never block
session start: they are silently skipped, and the skip count is shown in the
startup banner.

At session start, AgentOS also announces what it can now do:

```
AgentOS가 파일을 찾고·읽고·고치고(write/edit) 명령을 실행할(bash) 수 있습니다.
되돌리기 어려운 도구는 실행 전마다 승인을 요청합니다.
```

For uninterrupted interactive work, opt in explicitly with `--yolo`:

```bash
agentos --yolo
agentos run --yolo
```

YOLO skips approval prompts for `write`, `edit`, and `bash` and removes the
per-turn tool-call cap. It can affect files outside the project through
`bash`; use `Esc`/`Ctrl+C` to cancel and omit `--yolo` to return to the default
approval mode. `--yolo` is intentionally unavailable with `--once`.

### 도구 (Tools)

AgentOS offers the model seven tools, all boundary-checked against the
session's working directory (`cwd`) through one shared resolver:

| 도구 | 역할 | 승인 |
|---|---|---|
| `read` | Read a file. | 불필요 (opt-in via `AGENTOS_TOOL_READ_CONFIRM`) |
| `list` | List a directory's entries. | 불필요 |
| `glob` | Find files by name pattern. | 불필요 |
| `grep` | Search file contents by regex. | 불필요 |
| `write` | Create or overwrite a file. | **필수 — 매 호출** |
| `edit` | Replace one exact, unique string in a file. | **필수 — 매 호출** |
| `bash` | Run a shell command from `cwd`. | **필수 — 매 호출** |

By default, `write`, `edit`, and `bash` ask for approval before every single
call, independent of any environment variable. If no approval callback is
available, the call is denied rather than run unattended. The explicit
interactive `--yolo` mode is the only exception.

**The approval screen shows the full action, not a truncated summary.** A
`bash` call displays the entire command, wrapped rather than cut off at a
fixed character limit — a head-truncated summary would hide exactly the kind
of destructive trailing command (`&& rm -rf ...`) a user most needs to see.
A `write` call states whether it creates a new file or overwrites an
existing one (with its current size). An `edit` call shows the old and new
text side by side. When several tool calls happen in one turn, the screen
also shows a running count ("이번 턴 N번째 도구 승인") so repeated approvals
stay visible instead of becoming a reflex.

In the TUI, a long action description scrolls inside its own region of the
popup rather than growing the popup itself — the 승인 (approve) / 거부 (deny)
options always stay on screen, no matter how long the command or diff is.

**`bash`는 샌드박스가 아닙니다.** Unlike the other six tools, an approved
`bash` command can affect files outside the session's working directory —
pinning `cwd` only sets where the process starts, not what it may touch.
매 호출 승인이 유일한 실질 통제선이며, 네트워크 차단이나 파일시스템 격리는
제공하지 않습니다. The approval screen states this before every `bash` call.

Denying a tool call ends the turn immediately: nothing changes, and the
message tells you so and suggests retrying with a different request. Hitting
the per-turn tool-call limit (10 calls) behaves the same way — split a large
request into smaller ones if you hit it.

At session start, a one-line banner reports what loaded:

```
부트스트랩 컨텍스트: 2개 파일, 3개 스킬 로드됨 — /status로 확인
```

Run `/status` at any time to see the exact file paths and skill names that
were loaded into the current session.

**Opt out**: set `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1` to disable this feature
entirely for a session — no context files or skills are discovered, and no
bootstrap system message is created.

### `@`-include expansion

A line that is *only* `@<path>` (matching Claude Code's `CLAUDE.md` include
syntax) is replaced with the referenced file's content. Relative paths
resolve against the including file's directory; includes are recursive up
to 5 levels deep.

**Trust boundary**: an included path is only honored when it resolves
inside the directory the including file was found in (or a subdirectory of
it) — never an ancestor, never an absolute path, never `~`. This is
narrower than Claude Code's own `@~/anything` support, on purpose: a
context file discovered by walking untrusted ancestor directories must not
be able to pull in and leak arbitrary files (`@~/.ssh/id_rsa`,
`@/etc/passwd`) outside the directory it was found in. Anything that
escapes this boundary, is missing, is circular, or exceeds the depth limit
is replaced inline with a marker instead of failing the whole file:

```
[INCLUDE_BLOCKED: @../outside/secret.md escapes trusted context root]
[INCLUDE_SKIPPED: @a.md already included (circular reference)]
[INCLUDE_BLOCKED: @f.md exceeds max include depth 5]
```

Expansion happens before prompt-injection scanning and the size cap below,
so included content is covered by both.

### Prompt-injection scanning and size caps

Because ancestor-directory discovery can pull in an `AGENTS.md`/`CLAUDE.md`
you did not author (a shared monorepo root, a cloned untrusted repository),
every discovered file's content is scanned for prompt-injection patterns
before it is added to the bootstrap system message. Patterns cover classic
"ignore previous instructions" injection, role-play/identity hijack, known
command-and-control framework names (Cobalt Strike, Sliver, Havoc,
Metasploit, etc.), and invisible-unicode obfuscation. This is a best-effort,
regex-based advisory guard, not a guarantee — a sufficiently obfuscated
payload can still slip through.

If a file matches a threat pattern, its content is **not** loaded. Instead
the system message contains:

```
[BLOCKED: AGENTS.md contained potential prompt injection (known_c2_framework). Content not loaded.]
```

Run `/status` to see which files were blocked and which pattern categories
matched (an attack-type identifier, not the literal matched text). If a
normal, non-malicious file is blocked (a false positive), use the pattern
category shown in `/status` to find and edit the offending wording in that
file — the file loads normally again on the next session. You do not need
to reach for `AGENTOS_SKIP_CONTEXT_BOOTSTRAP=1` (which disables bootstrap
entirely) just to recover from a single false positive.

Separately, any context file larger than 20,000 characters is capped: only
the head and tail are kept, with a marker noting how much was kept and the
original file path, e.g. `[...truncated AGENTS.md: kept 12000+6000 of
25000 chars. See full file at: /path/to/AGENTS.md]`. This keeps one
oversized file from eating a session's entire token budget. Truncated
files are also listed in `/status`.

## Hooks

Hooks are built-in declarative policies from `AGENTOS_HOME/config.toml` with
schema `agentos.hooks/v1`.

Built-ins:

- `trim_whitespace`
- `reject_empty`
- `max_input_chars`
- `prepend_context_file`
- `record_turn_metrics`

`prepend_context_file` is disabled by default. It accepts only a direct `.md`
basename under `AGENTOS_HOME/context`, rejects symlinks, and enforces a 65536
byte limit. Hooks cannot run shell commands, import Python modules, or access
raw token, raw key, raw environment, or raw provider stderr.

## Sessions

Sessions are local user data under `AGENTOS_HOME/sessions`:

- `<uuid>.jsonl` — legacy `agentos.session/v1` append-only CLI event log
  (`input_received`, wrapped provider events). Still written on every turn
  for `/tree` and inspection commands.
- `<uuid>.meta.json` — session metadata (provider, mode, timestamps).
- `<uuid>.conversation-events.jsonl` — durable `agentos.conversation-session/v1`
  `turn_committed(sequence=N)` log: each line carries the full post-turn
  conversation state. Written (fsync'd) *before* the paired snapshot below,
  so a crash between the two is always recoverable by replay.
- `<uuid>.conversation-snapshot.json` — the latest conversation state,
  written to `.tmp`, fsync'd, atomically renamed into place, then the
  containing directory is fsync'd. Resume reads this snapshot plus any
  `turn_committed` events newer than it; a missing, unreadable, or
  interrupted-rename (orphaned `.tmp`) snapshot is simply treated as absent
  and rebuilt entirely from the events log.

A session created before this conversation-runtime existed has only the
first two files. Resuming it migrates the legacy JSONL log read-only (it is
never written to using the new protocol): assistant/tool text is recovered
verbatim from `message_delta`/`tool_result` payloads, while each legacy
user turn — whose prompt text was never persisted in a recoverable form,
only its length — is represented as an explicitly labeled placeholder
message (`[legacy session: original prompt text was not persisted, ...]`).
A migrated legacy session always resumes via full replay and never attaches
a provider continuation, since the legacy format predates continuation
entirely — this is the same "no reuse" property every fresh session gets
after a real process restart (see Recovery Matrix above).

There is no automatic deletion. `session delete` and `session prune` preview
their target and require an interactive confirmation or `--yes`. Without a TTY
and without `--yes`, deletion exits `2` and changes nothing; deleting a
session removes all four file variants above.

## Credential Boundary

AgentOS does not store API keys, raw token values, raw provider stderr, provider auth file paths, raw callback query values, or raw response bodies. AgentOS owns native Codex auth/transport: the native provider is the canonical `codex` path, using a documented OpenAI Codex account-login flow (browser login by default, with device-code as an automatic fallback in the same login flow) and a native streaming transport. The external CLI compatibility path (`agentos/llm/providers/codex_cli.py`) is a recovery-only debug/rollback path, selected only when native auth/transport fails explicitly; it is never the default interactive path.

## Native Codex Sign-In (`--provider codex`)

`agentos llm login --provider codex` (or `/login` in the TUI) starts the
AgentOS-owned account-login flow:

1. AgentOS attempts **browser login** by default: it opens a local callback
   server and your browser to the Codex sign-in page.
2. If the browser cannot be opened, AgentOS falls back to **device-code**
   sign-in automatically, in the same login flow — no separate command is
   required.
3. After sign-in, run `agentos llm status --provider codex --json` to
   confirm `authenticated: true`.

Session refresh is transparent: an expired access token is refreshed from
the stored refresh token the next time status or a run is checked, with no
user action required unless the refresh token itself has expired (in which
case `agentos llm login --provider codex` is required again).

`agentos llm logout --provider codex` removes the local native Codex auth
record. Running it again when the session is **already logged out** is a
sanitized no-op success, not an error.

### Recovery-only debug path: `--provider codex-cli`

`--provider codex-cli` delegates to the previously-installed Codex CLI
instead of AgentOS-owned native auth/transport. It is not selected
automatically; use it only when native `codex` sign-in or streaming fails
and you need the older external-CLI path as a rollback while diagnosing the
issue.

### Opt-in real integration smoke

Unit tests use fake callback servers, fake device-code endpoints, and fake
transports — no network access. A real two-turn smoke test against your
authenticated Codex account only runs when you explicitly opt in:

```bash
AGENTOS_CODEX_INTEGRATION=1 uv run agentos llm status --provider codex --json
AGENTOS_CODEX_INTEGRATION=1 uv run pytest tests/test_codex_session_integration.py -q
```

## Native Claude Sign-In (`--provider claude`)

`agentos llm login --provider claude` starts the AgentOS-owned Claude
Pro/Max account-login flow:

1. AgentOS opens a local callback server and your browser to the Claude
   sign-in page. Unlike Codex, there is no device-code fallback — Anthropic
   does not publicly offer one, so a failed browser launch ends the login
   attempt directly.
2. After sign-in, run `agentos llm status --provider claude --json` to
   confirm `authenticated: true`.

Session refresh is transparent: an expired access token is refreshed from
the stored refresh token the next time status or a run is checked, with no
user action required unless the refresh token itself has expired (in which
case `agentos llm login --provider claude` is required again).

`agentos llm logout --provider claude` removes the local native Claude auth
record. Running it again when the session is **already logged out** is a
sanitized no-op success, not an error.

**이 통합은 Anthropic이 공식 지원을 문서화한 대상이 아니며, Anthropic이 예고 없이 이
로그인 방식을 차단할 수 있습니다.** AgentOS는 Anthropic이 공식 Claude Code CLI에
발급한 OAuth client_id를 재사용하고, Claude Code로 인식되는 요청 헤더를 함께
보냅니다(client_secret이 없는 공개 OAuth 클라이언트이므로 이 값 자체는 비밀정보가
아닙니다). Anthropic이 이 방식을 차단하면 두 가지 다른 메시지 중 하나를 보게 됩니다:

- 일반 로그인 만료: "Claude 로그인이 만료되었습니다. 다시 로그인하세요." — `agentos
  llm login --provider claude`로 재로그인하면 해결됩니다.
- 정책 차단 추정: "Claude 로그인 연동이 Anthropic 정책 변경으로 차단되었을 수
  있습니다(알려진 리스크). 재로그인으로 해결되지 않으면 AgentOS 업데이트를
  확인하세요." — 이 경우 재로그인으로는 해결되지 않으며, 이는 버그가 아니라
  알려진 정책 리스크입니다.

Claude Messages는 Codex Responses API의 서버 측 대화 연속(`previous_response_id`)
기능이 없으므로, 매 턴 전체 대화 기록을 다시 전송합니다. WebSocket 전송도
지원하지 않으며 SSE(server-sent events) 스트리밍만 사용합니다.

AgentOS는 OAuth 요청에 pi와 같은 Claude Code identity headers 및 direct-browser
access header를 사용합니다. 도구 이름도 Claude Code 형식으로 보내고, 응답 도구
호출은 AgentOS registry 이름으로 복원합니다. 이 계약은 OAuth account-login에만
적용되며 Anthropic API key 지원을 추가하지 않습니다.

실제 Claude 계정 호출은 기본 테스트에서 절대 실행하지 않습니다. 로그인 상태에서
한 번 확인하려면 아래처럼 명시적으로 opt-in 하세요. 이 테스트는 `message_delta`
뒤 `done` event를 확인하며, 미인증이면 `STOP claude-session-integration
unauthenticated`와 종료 코드 2로 중단합니다.

```bash
AGENTOS_CLAUDE_INTEGRATION=1 uv run pytest tests/test_claude_session_integration.py -q
```

실제 요청 한도(HTTP 429)가 발생하면 AgentOS는 `Retry-After`의 유효한 대기 시간만
표시합니다. 대기 시간이 없거나 유효하지 않으면 "잠시 후 다시 시도하세요"를
표시합니다. 오류 본문, 인증 토큰, 원본 header 값은 복구 안내에 표시하지 않습니다.

Without `AGENTOS_CODEX_INTEGRATION=1`, these real-network checks do not run.
