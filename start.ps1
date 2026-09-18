# =====================================================================
# Smart Traffic Management System — Combined Bootstrap & Launcher
# Convenience wrapper delegating to scripts/setup.ps1 and scripts/run.ps1
# =====================================================================
param(
    [string]$PythonPath = '',
    [switch]$Lan,
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (-not $SkipInstall) {
    & (Join-Path $PSScriptRoot "scripts\setup.ps1") -PythonPath $PythonPath
    if ($LASTEXITCODE -ne 0) {
        throw "Environment setup failed."
    }
}

& (Join-Path $PSScriptRoot "scripts\run.ps1") -Lan:$Lan
