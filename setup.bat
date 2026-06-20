@echo off
chcp 65001 >nul
echo === goal-hook v1.0.3 安装 ===
echo.

set "PLUGIN_DIR=%~dp0"
set "SETTINGS=%USERPROFILE%\.claude\settings.json"

if not exist "%SETTINGS%" (
    echo ❌ 未找到 %SETTINGS%，请先运行一次 Claude Code
    pause
    exit /b 1
)

echo [1/2] 注册 marketplace ...
python -c "import json, sys; p=r'%SETTINGS%'; d=json.load(open(p,'r',encoding='utf-8')); d.setdefault('extraKnownMarketplaces',{})['goal-hook-marketplace']={'source':{'path':r'%PLUGIN_DIR%','source':'directory'}}; d.setdefault('enabledPlugins',{})['goal-hook@goal-hook-marketplace']=True; json.dump(d,open(p,'w',encoding='utf-8'),indent=2,ensure_ascii=False); print('✅ settings.json 已更新')" 2>&1
if errorlevel 1 (
    echo ❌ 更新失败，请手动编辑 %SETTINGS%
    pause
    exit /b 1
)

echo [2/2] 验证插件文件 ...
if exist "%PLUGIN_DIR%\hooks\hooks.json" (echo   ✅ hooks/hooks.json) else (echo   ❌ hooks/hooks.json 缺失)
if exist "%PLUGIN_DIR%\scripts\_goal_check.py" (echo   ✅ scripts/_goal_check.py) else (echo   ❌ scripts/_goal_check.py 缺失)
if exist "%PLUGIN_DIR%\.claude-plugin\plugin.json" (echo   ✅ .claude-plugin/plugin.json) else (echo   ❌ .claude-plugin/plugin.json 缺失)

echo.
echo === 安装完成 ===
echo 请重启 Claude Code 使插件生效。
echo 验证: 重启后 CC 启动日志中应显示 goal-hook 插件。
pause
