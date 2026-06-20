#!/usr/bin/env python3
"""goal-hook 一键安装 —— 自动注册 marketplace + 启用插件。"""
import json, os, sys

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")

if not os.path.exists(SETTINGS_PATH):
    print(f"ERROR: {SETTINGS_PATH} not found. Run Claude Code first.")
    sys.exit(1)

# Backup
with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
    original = f.read()
with open(SETTINGS_PATH + ".bak", "w", encoding="utf-8") as f:
    f.write(original)

settings = json.loads(original)

# Register marketplace
settings.setdefault("extraKnownMarketplaces", {})["goal-hook-marketplace"] = {
    "source": {"path": PLUGIN_DIR, "source": "directory"}
}
# Enable plugin
settings.setdefault("enabledPlugins", {})["goal-hook@goal-hook-marketplace"] = True

with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

# Verify
for f in ["hooks/hooks.json", "scripts/_goal_check.py", ".claude-plugin/plugin.json"]:
    fp = os.path.join(PLUGIN_DIR, f)
    status = "OK" if os.path.exists(fp) else "MISS"
    print(f"  [{status}] {f}")

print(f"\nInstalled from: {PLUGIN_DIR}")
print("Restart Claude Code to activate.")
