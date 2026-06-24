$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$specPath = Join-Path $repoRoot "packaging\heisenberg-network-monitor.spec"

Set-Location $repoRoot

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw "PyInstaller is not installed. Install requirements-dev first."
}

pyinstaller --noconfirm --clean $specPath

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable: $repoRoot\dist\HeisenbergNetworkMonitor\HeisenbergNetworkMonitor.exe"
