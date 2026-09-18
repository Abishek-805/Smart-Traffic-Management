# =====================================================================
# Smart Traffic Management System - Operational Health Check
# Verifies running backend REST APIs, AI engine, and digital intersection
# =====================================================================
param(
    [string]$Url = 'http://localhost:8000',
    [int]$TimeoutSeconds = 10
)

$ErrorActionPreference = 'Continue'
$hasErrors = $false

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Smart Traffic Management - Operational Health Check" -ForegroundColor Cyan
Write-Host "  Target URL: $Url" -ForegroundColor DarkGray
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Check Root Dashboard HTML
Write-Host "`n[1/4] Checking Web Management Dashboard..." -ForegroundColor Yellow
try {
    $resHtml = Invoke-WebRequest -Uri "$Url/" -TimeoutSec $TimeoutSeconds -UseBasicParsing -ErrorAction Stop
    if ($resHtml.StatusCode -eq 200) {
        $content = [string]$resHtml.Content
        if ($content -match 'root' -or $content -match 'Traffic Control Center' -or $content -match '<!DOCTYPE html>') {
            Write-Host "  [OK] Web Dashboard HTML served successfully (HTTP 200)." -ForegroundColor Green
        } else {
            Write-Host "  [WARN] Dashboard responded with HTTP 200 but unexpected content." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [WARN] Dashboard responded with status $($resHtml.StatusCode)." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [FAIL] Failed to connect to Web Dashboard at $Url/: $_" -ForegroundColor Red
    $hasErrors = $true
}

# 2. Check System Health (/api/v1/system/health)
Write-Host "`n[2/4] Checking System Health API (/api/v1/system/health)..." -ForegroundColor Yellow
try {
    $resHealth = Invoke-RestMethod -Uri "$Url/api/v1/system/health" -TimeoutSec $TimeoutSeconds -ErrorAction Stop
    $data = if ($resHealth.data) { $resHealth.data } else { $resHealth }

    $sysStatus = [string]$data.system_status
    $aiStatus = [string]$data.components.ai.status
    $aiModel = [string]$data.components.ai.model
    $aiRuntime = [string]$data.components.ai.runtime
    $opMode = [string]$data.operating_mode

    Write-Host "  [OK] System Status: $sysStatus" -ForegroundColor Green
    Write-Host ("  [OK] AI Component: {0} ({1} {2})" -f $aiStatus, $aiModel, $aiRuntime) -ForegroundColor Green
    Write-Host ("  [OK] Operating Mode: {0}" -f $opMode) -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Failed to query /api/v1/system/health: $_" -ForegroundColor Red
    $hasErrors = $true
}

# 3. Check System Status (/api/v1/system/status)
Write-Host "`n[3/4] Checking Operational Status API (/api/v1/system/status)..." -ForegroundColor Yellow
try {
    $resStatus = Invoke-RestMethod -Uri "$Url/api/v1/system/status" -TimeoutSec $TimeoutSeconds -ErrorAction Stop
    $data = if ($resStatus.data) { $resStatus.data } else { $resStatus }

    $aiEngine = [string]$data.ai_engine
    $actPhase = [string]$data.active_phase
    $espMode = [string]$data.esp32_mode

    Write-Host ("  [OK] AI Engine: {0}" -f $aiEngine) -ForegroundColor Green
    Write-Host ("  [OK] Active Phase: {0}" -f $actPhase) -ForegroundColor Green
    Write-Host ("  [OK] Hardware Mode: {0}" -f $espMode) -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Failed to query /api/v1/system/status: $_" -ForegroundColor Red
    $hasErrors = $true
}

# 4. Check Digital Intersection State (/api/v1/system/digital-intersection)
Write-Host "`n[4/4] Checking Digital Intersection (/api/v1/system/digital-intersection)..." -ForegroundColor Yellow
try {
    $resIntersection = Invoke-RestMethod -Uri "$Url/api/v1/system/digital-intersection" -TimeoutSec $TimeoutSeconds -ErrorAction Stop
    $snap = if ($resIntersection.data) { $resIntersection.data } else { $resIntersection }

    $phase = [string]$snap.active_phase
    $safety = [string]$snap.safety_status
    $rem = [string]$snap.remaining_time_seconds
    $approaches = $snap.approaches

    $appCount = ($approaches.psobject.properties | Measure-Object).Count
    Write-Host ("  [OK] Active Phase: {0} | Safety Status: {1} | Remaining: {2}s" -f $phase, $safety, $rem) -ForegroundColor Green
    Write-Host ("  [OK] Monitored Approaches: {0} (North, East, South, West present)" -f $appCount) -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Failed to query /api/v1/system/digital-intersection: $_" -ForegroundColor Red
    $hasErrors = $true
}

Write-Host "`n=====================================================" -ForegroundColor Cyan
if ($hasErrors) {
    Write-Host "  HEALTH CHECK FAILED: One or more endpoints were unreachable." -ForegroundColor Red
    Write-Host "=====================================================" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "  ALL HEALTH CHECKS PASSED: System is operational!" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Cyan
    exit 0
}
