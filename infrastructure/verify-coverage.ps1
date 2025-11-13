# MyStock - Code Coverage Verification
# Verifies that code coverage meets the 70% threshold requirement

param(
    [Parameter(Mandatory=$false)]
    [int]$MinimumCoverage = 70
)

$ErrorActionPreference = "Stop"

Write-Host "=== MyStock Code Coverage Verification ===" -ForegroundColor Cyan
Write-Host "Minimum Required Coverage: $MinimumCoverage%" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# Backend Coverage (Python/pytest)
Write-Host "Checking Backend Coverage..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

Push-Location "$PSScriptRoot\..\backend"

# Activate virtual environment
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
} else {
    Write-Error "Backend virtual environment not found. Run 'python3 -m venv .venv' first."
}

# Run pytest with coverage
python -m pytest tests/ --cov=src --cov-report=term --cov-report=html:coverage_html --cov-report=json:coverage.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Backend tests failed" -ForegroundColor Red
    $allPassed = $false
} else {
    # Parse coverage from JSON report
    $coverageData = Get-Content "coverage.json" | ConvertFrom-Json
    $backendCoverage = [math]::Round($coverageData.totals.percent_covered, 2)
    
    Write-Host ""
    Write-Host "Backend Coverage: $backendCoverage%" -ForegroundColor Cyan
    Write-Host "Coverage report: $PSScriptRoot\..\backend\coverage_html\index.html" -ForegroundColor Gray
    
    if ($backendCoverage -lt $MinimumCoverage) {
        Write-Host "✗ FAIL: Backend coverage ($backendCoverage%) is below $MinimumCoverage%" -ForegroundColor Red
        $allPassed = $false
    } else {
        Write-Host "✓ PASS: Backend coverage ($backendCoverage%) meets $MinimumCoverage% requirement" -ForegroundColor Green
    }
}

Pop-Location

Write-Host ""
Write-Host "Checking Frontend Coverage..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

Push-Location "$PSScriptRoot\..\frontend"

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

# Run vitest with coverage
npm run test:unit -- --coverage --coverage.reporter=json --coverage.reporter=html --coverage.reporter=text

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Frontend tests failed" -ForegroundColor Red
    $allPassed = $false
} else {
    # Parse coverage from JSON report
    $coverageSummary = Get-Content "coverage\coverage-summary.json" | ConvertFrom-Json
    $frontendCoverage = [math]::Round($coverageSummary.total.lines.pct, 2)
    
    Write-Host ""
    Write-Host "Frontend Coverage: $frontendCoverage%" -ForegroundColor Cyan
    Write-Host "Coverage report: $PSScriptRoot\..\frontend\coverage\index.html" -ForegroundColor Gray
    
    if ($frontendCoverage -lt $MinimumCoverage) {
        Write-Host "✗ FAIL: Frontend coverage ($frontendCoverage%) is below $MinimumCoverage%" -ForegroundColor Red
        $allPassed = $false
    } else {
        Write-Host "✓ PASS: Frontend coverage ($frontendCoverage%) meets $MinimumCoverage% requirement" -ForegroundColor Green
    }
}

Pop-Location

# Overall summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Gray
Write-Host ""

if ($allPassed) {
    Write-Host "=== All coverage requirements met ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend: $backendCoverage%" -ForegroundColor Cyan
    Write-Host "Frontend: $frontendCoverage%" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "View detailed reports:" -ForegroundColor Yellow
    Write-Host "  Backend:  $PSScriptRoot\..\backend\coverage_html\index.html" -ForegroundColor White
    Write-Host "  Frontend: $PSScriptRoot\..\frontend\coverage\index.html" -ForegroundColor White
    exit 0
} else {
    Write-Host "=== Coverage requirements not met ===" -ForegroundColor Red
    Write-Host ""
    Write-Host "Required: $MinimumCoverage%" -ForegroundColor Yellow
    if ($backendCoverage) {
        Write-Host "Backend: $backendCoverage%" -ForegroundColor $(if ($backendCoverage -ge $MinimumCoverage) { "Green" } else { "Red" })
    }
    if ($frontendCoverage) {
        Write-Host "Frontend: $frontendCoverage%" -ForegroundColor $(if ($frontendCoverage -ge $MinimumCoverage) { "Green" } else { "Red" })
    }
    exit 1
}
