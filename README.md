<div align="center">
  <img src="./readme_images/01-hero-banner.svg" alt="hello-goal" width="800">
</div>

# hello-goal v2.3.10

exit 2 Native BLOCK Signal + Dual-Channel API Error Recovery + /goal Hybrid Guardian. BLOCK uses exit code 2 + stderr (bypasses JSON validation, unaffected by native /goal evaluator's JSON validation failed). StopFailure channel recovers CC-level API errors (socket/429/503) unconditionally. Stop Phase 0 covers message-level errors (~85 patterns / 5-source detection). DeepSeek V4 thinking mode compatible. Language-agnostic. Zero external dependencies. Pure Python standard library.

[![Version](https://img.shields.io/badge/version-2.3.10-orange.svg)](./RELEASE_NOTES.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![LINUX DO](https://img.shields.io/badge/LINUX_DO-recognized-0A84FF?logo=linux&logoColor=white)](https://linux.do)

[English](./README.md) · [简体中文](./README_CN.md)

> This project is recognized by the [LINUX DO](https://linux.do) community.

## Table of Contents

<details>
<summary><strong>Click to expand</strong></summary>

- [Overview](#overview)
- [The Problem It Solves](#the-problem-it-solves)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Recommended Settings](#recommended-settings)
- [Architecture](#architecture)
- [Files](#files)
- [FAQ](#faq)
- [License](#license)

</details>

## Overview

Claude Code's `/goal` has three typical failure modes in long-running tasks:

1. **Interruption** — hook errors or API exceptions kill the `/goal` loop
2. **Abandonment** — the model wants to quit early due to fatigue, long context, or loss of confidence
3. **Standard downgrade** — the model silently lowers completion criteria ("good enough", "mostly done")

Additionally, **API errors** (socket disconnect, HTTP 429/502/503/500, rate limiting, overload, auth failures, etc.) can kill ANY task — `/goal` or not. hello-goal covers these through a **dual-channel** approach:

- **StopFailure event**: CC v2.1.78+ fires on API errors. `_goal_failure.py` uses `exit 2 + stderr` for unconditional BLOCK recovery.
- **Stop Phase 0**: Message-level API errors (~85 patterns / 5-source detection). Only matches short messages (<100 chars) and system transcript entries, avoiding false triggers from meta-discussion.

**hello-goal v2.3.10** BLOCK uses **exit code 2 + stderr** (CC's native block signal), bypassing JSON validation entirely. When running alongside CC's native /goal evaluator (which may output non-JSON with DeepSeek etc.), the native evaluator's `JSON validation failed` does not discard hello-goal's BLOCK. LLM semantic analysis auto-adapts DeepSeek V4 thinking mode. API unavailability state cache (120s TTL).

### Design Principle: Hardcoded JSON Output

```
LLM semantic analysis → True / False / None (internal decision only)
                            ↓
    _block("继续")              or          _pass()
                            ↓
    print('{"decision":"block","reason":"继续"}')  or  print('{}')
                            ↓
          ↑ Hardcoded JSON — never LLM-generated ↑
```

Unlike CC's native `/goal` evaluator (which may output non-JSON text when using third-party LLMs like DeepSeek), hello-goal's hook stdout is always deterministic, code-written JSON. The LLM response text from `_llm_check()` is parsed internally with `startswith("BLOCK")` / `startswith("PASS")` and never reaches stdout.

### v2.3 vs v2.2

| | v2.2 | v2.3 |
|---|---|---|
| JSON output | `sys.stdout.buffer.write()` + `sys.stdout.flush()` | `print(json.dumps(...))` through `sys.stdout` — CC captures reliably |
| Output principle | Verbose reason strings as hook feedback | Hardcoded JSON — LLM output never reaches stdout |
| Encoding | `sys.stdout.reconfigure(encoding="utf-8")` | Same — restored at startup via `_setup_encoding()` |
| Process exit | `sys.exit(0)` | `sys.exit(0)` |
| API defaults | Hardcoded `api.anthropic.com` + `claude-3-5-haiku` | No hardcoded defaults — reads from CC env vars only |
| API key env | `ANTHROPIC_API_KEY` only | Also reads `ANTHROPIC_AUTH_TOKEN` |
| stdin errors | Catches `JSONDecodeError` + `IOError` | Catches all `Exception` (incl. `UnicodeDecodeError`) |
| BLOCK reason | Verbose diagnostic strings (~80 chars) | `"继续"` — 2 characters, minimal |
| Hook timeout | 60s | 30s |
| Native evaluator coexistence | Concurrent, may conflict | Concurrent — hardcoded JSON ensures independent validation |

### v2.2 vs v2.1

| | v2.1 | v2.2 |
|---|---|---|
| API error recovery | `/goal` only (Phase 1.5) | Global (Phase 0), before /goal check |
| Non-/goal API errors | PASS (task interrupted) | BLOCK (auto-recover) |
| Phase order | /goal → interrupt → API → behavioral+LLM | API → /goal → interrupt → behavioral+LLM |

### v2.1 vs v2.0

| | v2.0 | v2.1 |
|---|---|---|
| Decision model | Structural score hard threshold (≥50%→BLOCK) | All suspicious scores → LLM semantic analysis |
| False positive risk | Behavioral signals can misclassify wind-down as stall | LLM distinguishes genuine completion from abandonment |
| LLM calls | ~10% of turns (fuzzy zone only) | All suspicious turns (ensures correctness) |
| Complexity | 4 phases (Phase 2/3/4 with threshold adjustment) | 3 phases (unified Phase 2: signals + LLM) |

## The Problem It Solves

| Scenario | Without hello-goal | With hello-goal v2.3.10 |
|----------|-------------------|---------------------|
| API error (~85 patterns/9 categories) in any session | Task permanently interrupted | Phase 0 detects → auto-recover BLOCK |
| `/goal` hook error mid-task | Session terminates | Detects abnormal stop_reason → BLOCK |
| Model fatigue / wants to quit | Native evaluator passes | Structural signals + LLM confirm → BLOCK |
| Model downgrades completion standard | Low-quality "done" | Structural analysis detects stall → BLOCK |
| Post-compaction disorientation | Model forgets goal | PostCompact refreshes detection state |
| Normal session (no API error) | — | Zero interference, immediate pass |

## How It Works

```
Stop Hook fires
  │
  ├─ Phase 0 (Global): All-Type API Error Detection
  │   ├─ Match ~85 patterns / 9 categories: connection, HTTP, rate-limit, overload...
  │   ├─ DeepSeek V4 specific: thinking mode compat, reasoning_content, gateway errors
  │   ├─ Sources: stop_reason, assistant msg, transcript tail, API availability cache
  │   └─ API error detected → BLOCK (auto-resume, regardless of /goal mode)
  │
  ├─ Phase 1: /goal Detection (CC native markers + user commands + cache-first)
  │   ├─ Signal A: CC native "Goal set:" / "Goal cleared:" markers
  │   ├─ Signal B: User /goal command parsing (backup)
  │   ├─ Signal C: stop_hook_summary entries (confirming only)
  │   └─ Not /goal → PASS (zero interference)
  │
  ├─ Phase 2: Interruption Recovery
  │   └─ stop_reason != "end_turn" → BLOCK
  │
  └─ Phase 3: Behavioral Signals + LLM Semantic Analysis (unified hybrid)
      ├─ Signal 1: No tool calls in last turn        +30%
      ├─ Signal 2: Trend collapse (msg+tool decline)  +25%
      ├─ Signal 3: Stuck loop (3 turns same tools)    +20%
      ├─ Signal 4: Read-only stall (5 turns no writes) +15%
      ├─ score < 0.20 → PASS (no behavioral concern)
      └─ score ≥ 0.20 → LLM semantic analysis (with behavioral context)
          ├─ Lightweight model analyzes last_assistant_message + behavioral signals
          ├─ Distinguishes genuine completion from premature abandonment
          ├─ BLOCK → continue    PASS → allow stop
          └─ API unavailable → conservative BLOCK
  └─ Global Exception Guard: unhandled internal error → BLOCK
```

All BLOCK decisions use **exit code 2 + stderr** (CC's native block signal, bypassing JSON validation). PASS decisions use exit 0 + empty JSON `{}`. The LLM semantic analysis result only determines which branch is taken.

### Why not keywords/regex

There are 200+ languages. A model can express "I give up" in any of them. Keyword regex is neither exhaustive nor maintainable.

v2.3.3's behavioral analysis **doesn't read text content** — it scores tool call patterns, message length trends, and turn structure from the transcript. These signals are identical in every language. The LLM semantic analysis provides the final decision on all suspicious turns, handling any language natively.

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/code) installed and configured
- Python 3

### Install

```bash
git clone https://github.com/hellowind777/hello-goal.git
cd hello-goal
python setup.py
```

Restart Claude Code. Done.

### Manual Install

Clone the repo and add to `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "hello-goal@hello-goal-marketplace": true
  },
  "extraKnownMarketplaces": {
    "hello-goal-marketplace": {
      "source": {
        "path": "/path/to/hello-goal",
        "source": "directory"
      }
    }
  }
}
```

### Verify

The `setup.py` script validates that all plugin files are in place:

```
[1/3] Installing to ~/.claude/plugins/local-marketplaces/hello-goal-marketplace/plugins/hello-goal ...
[2/3] Registering in settings.json ...
[3/3] Verifying ...
  [OK] hooks/hooks.json
  [OK] scripts/_goal_guard.py
  [OK] .claude-plugin/plugin.json

Installed: .../hello-goal-marketplace
Restart Claude Code to activate.
```

## Usage

**Your GOAL_PROMPT needs no plugin-specific code.** Just describe the task objective and acceptance criteria.

```
/goal follow the prompt
```

The plugin monitors automatically, blocking premature termination and keeping `/goal` running until genuine completion. API errors are also auto-recovered in any session.

## Recommended Settings

```json
"CLAUDE_CODE_STOP_HOOK_BLOCK_CAP": "1000"
```

Claude Code v2.1.143+ enforces a maximum of 8 consecutive Stop hook blocks. Raise this to prevent legitimate long-running goal tasks from being killed.

## Architecture

```
hooks/hooks.json
├── Stop (command, 30s)          ← Core guardian: 4-phase analysis → exit 2
├── StopFailure (command, 3s)    ← API error recovery: CC-level errors → exit 2
├── SessionStart (command, 5s)   ← Stale state cleanup, session init
└── PostCompact (command, 3s)    ← Post-compaction detection cache refresh

scripts/_goal_guard.py (~850 lines, zero dependencies)
├── handle_stop()           ← Phase 0-3 main logic
├── _detect_api_error()     ← 5-source API error detection (~85 patterns + state cache)
├── _detect_goal_active()   ← Three-tier /goal detection (markers + commands + summary)
├── _structural_score()     ← Behavioral signal weighting (4 signals)
├── _llm_check()            ← LLM semantic analysis (DeepSeek V4 thinking=disabled)
├── _is_api_available()     ← API reachability check (120s cache)
├── _block()                ← exit 2 + stderr (CC native block signal)
└── _pass()                 ← exit 0 + empty JSON {}

scripts/_goal_failure.py (18 lines, zero dependencies)
└── StopFailure handler     ← exit 2 + stderr unconditional BLOCK
```

## Files

| File | Purpose |
|------|---------|
| `plugins/hello-goal/hooks/hooks.json` | Four-hook registration (Stop + StopFailure + SessionStart + PostCompact) |
| `plugins/hello-goal/scripts/_goal_guard.py` | Hybrid guardian main script (full analysis) |
| `plugins/hello-goal/scripts/_goal_failure.py` | StopFailure safety net (6 lines, unconditional BLOCK) |
| `plugins/hello-goal/.claude-plugin/plugin.json` | Plugin metadata (v2.3.10) |
| `.claude-plugin/marketplace.json` | Marketplace manifest |
| `setup.py` | One-click cross-platform installer |

## FAQ

<details>
<summary><strong>Q: Does this interfere with non-/goal sessions?</strong></summary>

**A:** For API errors — no. The plugin catches them globally and auto-recovers, which is exactly what you want (a socket disconnect should not kill your task). For normal non-API-error stops in non-/goal sessions, it passes immediately with zero intervention.
</details>

<details>
<summary><strong>Q: Do I need to modify my GOAL_PROMPT?</strong></summary>

**A:** No. v2.3.3 auto-detects `/goal` state from CC native markers in the transcript. It does not depend on any status file written by your prompt.
</details>

<details>
<summary><strong>Q: How much does the LLM analysis cost?</strong></summary>

**A:** All turns with any behavioral signal (score ≥ 0.20) trigger LLM analysis. Each lightweight model call costs approximately $0.0005. A 200-turn `/goal` task with behavioral signals on every turn costs about $0.10 total. Turns without signals (score < 0.20) pass instantly with zero LLM cost.
</details>

<details>
<summary><strong>Q: Does this conflict with CC's native /goal evaluator?</strong></summary>

**A:** Both run in parallel as separate stop hooks. When the native evaluator produces non-JSON text, CC reports "JSON validation failed". hello-goal v2.3.10 resolves this with **exit 2 + stderr**: BLOCK uses CC's native exit code 2 signal (bypassing JSON validation), so the native evaluator's JSON failure does not discard hello-goal's BLOCK. The StopFailure channel additionally handles CC-level API errors.
</details>

<details>
<summary><strong>Q: Why exit 2 instead of JSON for BLOCK?</strong></summary>

**A:** CC's native /goal evaluator (using third-party LLMs like DeepSeek) may output non-JSON text, causing the entire Stop hook batch to fail with `JSON validation failed`. hello-goal uses exit code 2 + stderr (CC's native "block" signal) which doesn't require JSON parsing, isolating it from the native evaluator's JSON failures.
</details>

<details>
<summary><strong>Q: Does LLM semantic analysis work with DeepSeek V4?</strong></summary>

**A:** Yes. v2.3.6 resolves DeepSeek V4 thinking mode compatibility — semantic analysis requests auto-inject `thinking: {type: "disabled"}` to get clean text output, avoiding the issue where thinking blocks consume all tokens with no text response. A thinking-block fallback extraction provides additional protection.
</details>

<details>
<summary><strong>Q: Will it block a genuinely completed task?</strong></summary>

**A:** No. When the task is truly done, the LLM semantic analysis recognizes genuine completion (final report, test results, comprehensive summary) and returns PASS — even if behavioral signals (no tools, trend decline) are elevated. The LLM is explicitly instructed to distinguish task wind-down from premature abandonment.
</details>

<details>
<summary><strong>Q: What if the plugin itself hits an unexpected error?</strong></summary>

**A:** The main handler is wrapped in a global exception guard. Any unexpected internal error outputs a hardcoded BLOCK decision via `print()` — keeping the task running safely rather than crashing with a "JSON validation failed" error.
</details>

## License

This project is licensed under the [Apache-2.0 License](./LICENSE).

---

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/hellowind777/hello-goal?style=social)
![GitHub forks](https://img.shields.io/github/forks/hellowind777/hello-goal?style=social)

</div>
