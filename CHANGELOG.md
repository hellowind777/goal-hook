# Changelog

All notable changes to this project will be documented in this file.

## [2.3.6] - 2026-07-01

### Added
- API unavailability state cache (`_is_api_available` / `_mark_api_unavailable`): after LLM call fails, subsequent hooks within 120s TTL skip LLM and return BLOCK directly.
- State file directory multi-level fallback: `CLAUDE_PLUGIN_DATA` → `CLAUDE_PLUGIN_ROOT` → `TEMP` → script dir.

### Changed
- API error patterns expanded from ~10 to ~85, covering 9 categories: connection/network, HTTP status, rate-limit/quota, overload, auth, model/engine, internal errors, DeepSeek V4 specific, generic failures.
- DeepSeek V4 thinking mode compatibility: `_llm_check` auto-detects DeepSeek URLs and injects `thinking: {type: "disabled"}`.
- LLM text extraction now falls back to `thinking` blocks when no `text` block is present.
- `_llm_check` `max_tokens` increased from 10 to 100.

### Fixed
- LLM semantic analysis failing silently on DeepSeek V4 due to thinking mode consuming all tokens with no text output.
- State persistence failing when `CLAUDE_PLUGIN_DATA` environment variable is not set.

## [2.3.5] - 2026-06-28

### Added
- StopFailure safety net (`_goal_failure.py`, 6 lines): unconditional BLOCK on any Stop hook failure.
- `StopFailure` event registration in `hooks.json` (3s timeout).

### Changed
- Hardcoded JSON output via `print()` through `sys.stdout` — eliminates LLM-generated JSON validation errors.
- `ANTHROPIC_AUTH_TOKEN` support in addition to `ANTHROPIC_API_KEY`.
- `stdin` exception handling now catches all `Exception` types including `UnicodeDecodeError`.
- BLOCK reason shortened to `"继续"` (2 characters).

## [2.3.3] - 2026-06-28

### Changed
- JSON output switched to `print()` through `sys.stdout` for reliable CC capture.
- Removed hardcoded API defaults — reads only from CC environment variables.
- Hook timeout reduced from 60s to 30s.

### Fixed
- Native evaluator JSON validation conflict resolved via hardcoded JSON principle.

## [2.3.1] - 2026-06-27

### Changed
- JSON output hardened with `os.write(fd=1)`.
- Reason shortened to `"继续"`.
- DeepSeek compatibility improvements.
- Version/docs synchronized.

## [2.2.1] - 2026-06-26

### Fixed
- Stop hook timeout hardening: 12s → 60s + flush + time budget protection + double-layer exception guard.

## [2.2.0] - 2026-06-25

### Added
- Global API error auto-recovery (Phase 0): socket disconnect, 429, 502, 503 trigger BLOCK regardless of /goal mode.

## [2.1.2] - 2026-06-24

### Added
- Stop hook global exception guard.

## [2.1.1] - 2026-06-23

### Changed
- Goal detection rewritten with three-tier signal system (CC native markers + user commands + summary).
- Unified hybrid decision model (behavioral signals + LLM semantic analysis).
- Zero false positives for non-/goal sessions.

## [2.1.0] - 2026-06-22

### Changed
- Architecture upgrade: behavioral signals always pass through LLM semantic analysis for final decision.
- Reduced false positive risk from behavioral-only threshold model.

## [2.0.0] - Initial Release

### Added
- Stop hook with behavioral structural scoring (4 signals).
- /goal state detection from transcript.
- Interruption recovery (abnormal stop_reason → BLOCK).
