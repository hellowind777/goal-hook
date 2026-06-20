# goal-hook v1.0.3 安装脚本 (PowerShell)
$ErrorActionPreference = "Continue"
Write-Host "=== goal-hook v1.0.3 ===" -ForegroundColor Cyan

$pluginDir = $PSScriptRoot
$settingsPath = "$env:USERPROFILE\.claude\settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Host "ERROR: $settingsPath not found. Run Claude Code first." -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Backing up settings.json ..."
Copy-Item $settingsPath "$settingsPath.bak"

Write-Host "[2/3] Registering marketplace and enabling plugin ..."
$settings = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json

$marketplace = @{
    source = @{
        path = $pluginDir
        source = "directory"
    }
}
$settings.extraKnownMarketplaces | Add-Member -Name "goal-hook-marketplace" -Value $marketplace -MemberType NoteProperty -Force
$settings.enabledPlugins | Add-Member -Name "goal-hook@goal-hook-marketplace" -Value $true -MemberType NoteProperty -Force

$settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
Write-Host "  settings.json updated" -ForegroundColor Green

Write-Host "[3/3] Verifying plugin files ..."
$ok = $true
@("hooks\hooks.json", "scripts\_goal_check.py", ".claude-plugin\plugin.json") | ForEach-Object {
    $f = Join-Path $pluginDir $_
    if (Test-Path $f) { Write-Host "  OK  $_" -ForegroundColor Green }
    else { Write-Host "  MISS  $_" -ForegroundColor Red; $ok = $false }
}

if ($ok) {
    Write-Host "`nDone. Restart Claude Code." -ForegroundColor Cyan
} else {
    Write-Host "`nSome files missing. Check the plugin directory." -ForegroundColor Red
}
