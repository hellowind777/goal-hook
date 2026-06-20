# goal-hook v1.0.3 安装脚本 (PowerShell)
$ErrorActionPreference = "Stop"
Write-Host "=== goal-hook v1.0.3 安装 ===" -ForegroundColor Cyan

$pluginDir = $PSScriptRoot
$settingsPath = "$env:USERPROFILE\.claude\settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Host "❌ 未找到 $settingsPath，请先运行一次 Claude Code" -ForegroundColor Red
    exit 1
}

Write-Host "[1/2] 注册 marketplace ..."
try {
    $settings = Get-Content $settingsPath -Encoding UTF8 | ConvertFrom-Json -Depth 10 -AsHashtable

    if (-not $settings["extraKnownMarketplaces"]) {
        $settings["extraKnownMarketplaces"] = @{}
    }
    $settings["extraKnownMarketplaces"]["goal-hook-marketplace"] = @{
        source = @{
            path = $pluginDir
            source = "directory"
        }
    }

    if (-not $settings["enabledPlugins"]) {
        $settings["enabledPlugins"] = @{}
    }
    $settings["enabledPlugins"]["goal-hook@goal-hook-marketplace"] = $true

    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
    Write-Host "  ✅ settings.json 已更新" -ForegroundColor Green
} catch {
    Write-Host "  ❌ 更新失败: $_" -ForegroundColor Red
    Write-Host "  请手动编辑 $settingsPath"
    exit 1
}

Write-Host "[2/2] 验证插件文件 ..."
@("hooks\hooks.json", "scripts\_goal_check.py", ".claude-plugin\plugin.json") | ForEach-Object {
    $f = Join-Path $pluginDir $_
    if (Test-Path $f) { Write-Host "  ✅ $_" -ForegroundColor Green }
    else { Write-Host "  ❌ $_ 缺失" -ForegroundColor Red }
}

Write-Host "`n=== 安装完成 ===" -ForegroundColor Cyan
Write-Host "请重启 Claude Code 使插件生效。"
