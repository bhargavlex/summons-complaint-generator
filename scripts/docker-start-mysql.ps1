# Start MySQL only. Run from project root:
#   .\scripts\docker-start-mysql.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
docker compose -f docker-compose.yml up -d mysql
if ($LASTEXITCODE -eq 0) { Write-Host "MySQL started. Port 3307 (user appuser, password apppass, db appdb)" }
