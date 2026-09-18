# =====================================================================
# Smart Traffic Management System — Production Launcher
# Launches the combined FastAPI server & Web Control Center
# =====================================================================
param(
    [string]$HostAddress = '127.0.0.1',
    [int]$Port = 8000,
    [switch]$Lan
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location -LiteralPath $repoRoot

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment not found at '$venvPython'. Please run .\scripts\setup.ps1 first."
    exit 1
}

$bindAddress = if ($Lan) { '0.0.0.0' } else { $HostAddress }
$env:CAMERA_WS_PORT = [string]$Port

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Smart Traffic Management Control Center" -ForegroundColor Cyan
Write-Host "  Bind Address: $bindAddress : $Port" -ForegroundColor DarkGray
Write-Host "  Hardware Mode: Simulation (Virtual Lights Active)" -ForegroundColor DarkGray
Write-Host "=====================================================" -ForegroundColor Cyan

if ($bindAddress -eq '0.0.0.0') {
    Write-Host "`nServer available across local network at:" -ForegroundColor Green
    Write-Host "  Local:   http://localhost:$Port" -ForegroundColor White
    Write-Host "  LAN:     http://<YOUR_LAN_IP>:$Port" -ForegroundColor White
} else {
    Write-Host "`nServer running locally at:" -ForegroundColor Green
    Write-Host "  URL:     http://localhost:$Port" -ForegroundColor White
}

Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor Yellow

& $venvPython run.py --host $bindAddress --port $Port
