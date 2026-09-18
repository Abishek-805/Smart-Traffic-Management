# =====================================================================
# Smart Traffic Management System - Automated Setup Bootstrap
# Idempotent developer setup script for Windows (PowerShell)
# =====================================================================
param(
    [string]$PythonPath = '',
    [switch]$SkipWebBuild
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location -LiteralPath $repoRoot

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Smart Traffic Management - Environment Setup" -ForegroundColor Cyan
Write-Host "  Repository Root: $repoRoot" -ForegroundColor DarkGray
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Locate and Verify Python
Write-Host "`n[1/7] Verifying Python runtime..." -ForegroundColor Yellow
$pyExe = $null

if ($PythonPath -and (Test-Path $PythonPath)) {
    $pyExe = (Resolve-Path $PythonPath).Path
} elseif (Test-Path "$repoRoot\.venv\Scripts\python.exe") {
    $pyExe = "$repoRoot\.venv\Scripts\python.exe"
    Write-Host "  Found existing local .venv Python." -ForegroundColor DarkGray
} else {
    # Probe candidate locations
    $candidates = @(
        "C:\Users\$env:USERNAME\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            $pyExe = $cand
            break
        }
    }

    if (-not $pyExe) {
        if (Get-Command python -ErrorAction SilentlyContinue) {
            $pyExe = (Get-Command python).Source
        } elseif (Get-Command py -ErrorAction SilentlyContinue) {
            $pyExe = "py"
        }
    }
}

if (-not $pyExe) {
    Write-Error "Python is not installed or not found. Please install Python 3.12 (64-bit) from https://www.python.org/downloads/."
    exit 1
}

$versionRaw = & $pyExe -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'
Write-Host "  Using Python: $versionRaw ($pyExe)" -ForegroundColor Green

# 2. Verify Node.js and npm
Write-Host "`n[2/7] Verifying Node.js and npm..." -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js not found on PATH. Please install Node.js 20.x or 22.x LTS from https://nodejs.org/."
    exit 1
}
$nodeVer = & node -v
Write-Host "  Found Node.js: $nodeVer" -ForegroundColor Green

if (-not (Get-Command npm -ErrorAction SilentlyContinue) -and -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    Write-Error "npm not found on PATH. Please ensure npm is installed with Node.js."
    exit 1
}
$npmVer = & npm.cmd -v 2>$null
if (-not $npmVer) {
    $npmVer = & npm -v
}
Write-Host "  Found npm: $npmVer" -ForegroundColor Green

# 3. Create or Verify Virtual Environment
Write-Host "`n[3/7] Setting up Python virtual environment (.venv)..." -ForegroundColor Yellow
$venvDir = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "  Creating new virtual environment in $venvDir..." -ForegroundColor DarkGray
    & $pyExe -m venv $venvDir
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        Write-Error "Failed to create Python virtual environment in $venvDir."
        exit 1
    }
    Write-Host "  Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "  Existing virtual environment detected at $venvDir." -ForegroundColor Green
}

# 4. Install Python Dependencies
Write-Host "`n[4/7] Installing backend Python dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install -r (Join-Path $repoRoot "requirements-dev.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Python dependencies from requirements-dev.txt."
    exit 1
}
Write-Host "  Backend Python dependencies installed." -ForegroundColor Green

# 5. Setup Web UI Dependencies and Build Static SPA
Write-Host "`n[5/7] Setting up frontend Web UI (web-ui)..." -ForegroundColor Yellow
$webUiDir = Join-Path $repoRoot "web-ui"
Push-Location $webUiDir
try {
    $webModules = Join-Path $webUiDir "node_modules"
    if (-not (Test-Path $webModules)) {
        Write-Host "  Installing frontend npm packages..." -ForegroundColor DarkGray
        & npm.cmd install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "npm install failed in web-ui."
            exit 1
        }
    } else {
        Write-Host "  web-ui/node_modules present." -ForegroundColor Green
    }

    if (-not $SkipWebBuild) {
        Write-Host "  Building production frontend assets (web-ui/dist)..." -ForegroundColor DarkGray
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) {
            Write-Error "npm run build failed in web-ui."
            exit 1
        }
        Write-Host "  Frontend assets compiled successfully in web-ui/dist." -ForegroundColor Green
    }
} finally {
    Pop-Location
}

# 6. Environment Configuration (.env)
Write-Host "`n[6/7] Validating environment configuration (.env)..." -ForegroundColor Yellow
$envPath = Join-Path $repoRoot ".env"
$envExample = Join-Path $repoRoot ".env.example"
if (-not (Test-Path $envPath)) {
    if (Test-Path $envExample) {
        Copy-Item -LiteralPath $envExample -Destination $envPath
        Write-Host "  Created .env from .env.example (default local settings)." -ForegroundColor Green
    } else {
        Write-Warning "Neither .env nor .env.example was found. Server will use built-in defaults."
    }
} else {
    Write-Host "  Existing .env configuration found." -ForegroundColor Green
}

# 7. Model Weights Validation
Write-Host "`n[7/7] Validating YOLOv8n vision model weights..." -ForegroundColor Yellow
$modelPathRoot = Join-Path $repoRoot "yolov8n.pt"
$modelPathModels = Join-Path $repoRoot "models\yolov8n.pt"

if ((Test-Path $modelPathRoot) -or (Test-Path $modelPathModels)) {
    Write-Host "  Found YOLOv8n model weights file." -ForegroundColor Green
} else {
    Write-Host "  Model weights not found locally. Downloading official YOLOv8n weights..." -ForegroundColor DarkGray
    & $venvPython -c 'from ultralytics import YOLO; YOLO("yolov8n.pt")'
    if (-not (Test-Path $modelPathRoot) -and -not (Test-Path $modelPathModels)) {
        Write-Error "Automatic model acquisition failed. Please download yolov8n.pt into the repository root manually."
        exit 1
    }
    Write-Host "  YOLOv8n weights acquired successfully." -ForegroundColor Green
}

# External Services note
Write-Host ""
Write-Host "--- Services and Deployment Mode Note ---" -ForegroundColor Cyan
Write-Host "Combined Local Server: Redis is NOT required (in-memory state active)." -ForegroundColor DarkGray
Write-Host "Hardware Actuation: Simulation mode active (no physical ESP32 required)." -ForegroundColor DarkGray

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE! The system is ready to run." -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start the server:   powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1" -ForegroundColor White
Write-Host "  2. Check health:       powershell -ExecutionPolicy Bypass -File .\scripts\health-check.ps1" -ForegroundColor White
Write-Host "  3. Run test suite:     .\.venv\Scripts\python.exe -m pytest -q" -ForegroundColor White
