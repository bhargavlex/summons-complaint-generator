# PowerShell script to run field extraction in Docker container
# Usage: .\run_extraction_docker.ps1 [template_id]

param(
    [int]$TemplateId = 0
)

$CONTAINER_NAME = "fastapi_server"
$SCRIPT_PATH = "scripts/extract_template_fields.py"

if ($TemplateId -eq 0) {
    Write-Host "Running extraction for all active templates..." -ForegroundColor Cyan
    docker exec -it $CONTAINER_NAME python -m $SCRIPT_PATH
} else {
    Write-Host "Running extraction for template ID: $TemplateId" -ForegroundColor Cyan
    docker exec -it $CONTAINER_NAME python -m $SCRIPT_PATH $TemplateId
}
