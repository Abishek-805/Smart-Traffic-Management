param([string]$PythonPath = '', [switch]$Lan, [switch]$SkipInstall)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    if ($PythonPath) { & $PythonPath -m venv .venv }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { & py -3.12 -m venv .venv }
    else { throw 'Install Python 3.12 or supply -PythonPath with the full path to python.exe.' }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
if (-not $SkipInstall) {
    & $venvPython -m pip install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    Push-Location web-ui
    try {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Web dependency installation failed.' }
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
    } finally { Pop-Location }
}
$bindAddress = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
Write-Host 'Open http://localhost:8000 . Press Ctrl+C to stop. Hardware remains in simulation.'
& $venvPython run.py --host $bindAddress
