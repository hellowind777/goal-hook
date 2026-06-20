# Contributing

## Development

```bash
git clone <repo-url>
cd goal-hook
```

The plugin consists of three files:

| File | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin metadata |
| `hooks/hooks.json` | Hook registration |
| `scripts/_goal_check.py` | Status file checker |

## Testing

Install the plugin locally and run a `/goal` session with a GOAL_PROMPT that writes `in_progress` / `terminated`.

Verify:
1. Non-`/goal` sessions are unaffected (no file → pass)
2. `/goal` with `in_progress` blocks on Stop
3. `/goal` with `terminated` passes on Stop + cleans up file
4. Stale `in_progress` (>7 days) auto-expires

## Commit Convention

```
feat: description
fix: description
refactor: description
revert: description
```
