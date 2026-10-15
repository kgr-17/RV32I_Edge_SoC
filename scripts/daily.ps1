param()
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    python -B scripts/harness.py daily --supervised
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Get-Content -LiteralPath 'prompts/DAILY_RUN.md' -Encoding UTF8
    git status --short --branch
} finally {
    Pop-Location
}
