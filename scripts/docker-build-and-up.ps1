# Build backend and start all services. Run from project root:
#   .\scripts\docker-build-and-up.ps1
# Or from anywhere:
#   & "D:\New folder\summons-complaint-generator\scripts\docker-build-and-up.ps1"

$ErrorActionPreference = "Stop"
# Project root = parent of the folder containing this script (e.g. scripts -> project root)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ComposePath = Join-Path $ProjectRoot "docker-compose.yml"
if (-not (Test-Path $ComposePath)) {
    Write-Host "docker-compose.yml not found. Run this script from project root or where docker-compose.yml is."
    exit 1
}

Set-Location $ProjectRoot
$env:DOCKER_BUILDKIT = "0"
Write-Host "Building backend..."
docker compose -f docker-compose.yml build backend
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Starting services..."
docker compose -f docker-compose.yml up -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done. API: http://localhost:8000"
