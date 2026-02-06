# Run this script if you get: "open ... buildx\.lock: Access is denied"
# Option 1: Run PowerShell as Administrator, then:
#   cd "D:\New folder\summons-complaint-generator"
#   .\scripts\docker-fix-buildx-lock.ps1
# Option 2: In an elevated PowerShell:
#   Remove-Item $env:USERPROFILE\.docker\buildx\.lock -Force -ErrorAction SilentlyContinue

$lockPath = Join-Path $env:USERPROFILE ".docker\buildx\.lock"
if (Test-Path $lockPath) {
    try {
        Remove-Item $lockPath -Force
        Write-Host "[OK] Removed buildx lock file. Restart Docker Desktop, then run: docker compose build backend"
    } catch {
        Write-Host "[!] Could not remove lock (try running PowerShell as Administrator): $_"
        Write-Host "    Or manually delete: $lockPath"
    }
} else {
    Write-Host "No lock file at $lockPath"
    Write-Host "If build still fails: restart Docker Desktop, then run: docker compose build backend"
}
