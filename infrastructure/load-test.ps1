# MyStock - Load Testing Script
# Tests the application with 100 concurrent users using Artillery

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetUrl,
    
    [Parameter(Mandatory=$false)]
    [int]$Duration = 300,  # 5 minutes
    
    [Parameter(Mandatory=$false)]
    [int]$ArrivalRate = 20,  # 20 new users per second
    
    [Parameter(Mandatory=$false)]
    [int]$MaxVirtualUsers = 100
)

$ErrorActionPreference = "Stop"

Write-Host "=== MyStock Load Testing ===" -ForegroundColor Cyan
Write-Host "Target: $TargetUrl" -ForegroundColor Cyan
Write-Host "Duration: $Duration seconds" -ForegroundColor Cyan
Write-Host "Arrival Rate: $ArrivalRate users/second" -ForegroundColor Cyan
Write-Host "Max Concurrent Users: $MaxVirtualUsers" -ForegroundColor Cyan
Write-Host ""

# Check if Artillery is installed
try {
    artillery --version | Out-Null
} catch {
    Write-Host "Artillery not found. Installing..." -ForegroundColor Yellow
    npm install -g artillery@latest
}

# Create Artillery configuration
$artilleryConfig = @"
config:
  target: "$TargetUrl"
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: $Duration
      arrivalRate: $ArrivalRate
      maxVusers: $MaxVirtualUsers
      name: "Load test"
    - duration: 60
      arrivalRate: 2
      name: "Cool down"
  http:
    timeout: 30
  processor: "./load-test-processor.js"
  
scenarios:
  - name: "User registration and login"
    weight: 10
    flow:
      - post:
          url: "/api/auth/register"
          json:
            email: "{{ \`${faker.internet.email()}\` }}"
            password: "TestPassword123!"
            full_name: "{{ \`${faker.person.fullName()}\` }}"
          capture:
            - json: "\$.access_token"
              as: "authToken"
      - think: 2
      
  - name: "Authenticated user - Watchlist operations"
    weight: 30
    flow:
      - post:
          url: "/api/auth/login"
          json:
            email: "testuser@example.com"
            password: "TestPassword123!"
          capture:
            - json: "\$.access_token"
              as: "authToken"
      - get:
          url: "/api/watchlist"
          headers:
            Authorization: "Bearer {{ authToken }}"
      - post:
          url: "/api/watchlist"
          headers:
            Authorization: "Bearer {{ authToken }}"
          json:
            symbol: "{{ \`${['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'][Math.floor(Math.random() * 5)]}\` }}"
            memo: "Added by load test"
      - think: 3
      - get:
          url: "/api/watchlist"
          headers:
            Authorization: "Bearer {{ authToken }}"
      
  - name: "Authenticated user - Portfolio operations"
    weight: 30
    flow:
      - post:
          url: "/api/auth/login"
          json:
            email: "testuser@example.com"
            password: "TestPassword123!"
          capture:
            - json: "\$.access_token"
              as: "authToken"
      - get:
          url: "/api/portfolio"
          headers:
            Authorization: "Bearer {{ authToken }}"
      - post:
          url: "/api/portfolio"
          headers:
            Authorization: "Bearer {{ authToken }}"
          json:
            symbol: "{{ \`${['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'][Math.floor(Math.random() * 5)]}\` }}"
            quantity: "{{ \`${Math.floor(Math.random() * 100) + 1}\` }}"
            purchase_price: "{{ \`${(Math.random() * 500 + 50).toFixed(2)}\` }}"
            category: "{{ \`${['기술주', '성장주', '배당주'][Math.floor(Math.random() * 3)]}\` }}"
      - think: 3
      - get:
          url: "/api/portfolio/summary"
          headers:
            Authorization: "Bearer {{ authToken }}"
      
  - name: "Stock data queries"
    weight: 30
    flow:
      - get:
          url: "/api/stocks/search?q={{ \`${['Apple', 'Google', 'Microsoft', 'Amazon', 'Tesla'][Math.floor(Math.random() * 5)]}\` }}"
      - think: 1
      - get:
          url: "/api/stocks/quote/{{ \`${['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'][Math.floor(Math.random() * 5)]}\` }}"
      - think: 2
"@

$artilleryConfig | Out-File -FilePath "$PSScriptRoot\load-test.yaml" -Encoding UTF8

# Create processor script for dynamic data
$processorScript = @"
module.exports = {
  setJWT: setJWT
};

function setJWT(requestParams, context, ee, next) {
  // This function can be used to set JWT tokens dynamically
  return next();
}
"@

$processorScript | Out-File -FilePath "$PSScriptRoot\load-test-processor.js" -Encoding UTF8

# Create test user if needed
Write-Host "Creating test user..." -ForegroundColor Yellow
$testUserBody = @{
    email = "testuser@example.com"
    password = "TestPassword123!"
    full_name = "Load Test User"
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "$TargetUrl/api/auth/register" -Method POST -Body $testUserBody -ContentType "application/json" | Out-Null
    Write-Host "✓ Test user created" -ForegroundColor Green
} catch {
    Write-Host "Test user already exists or registration failed (continuing anyway)" -ForegroundColor Yellow
}

# Run Artillery load test
Write-Host ""
Write-Host "Starting load test..." -ForegroundColor Yellow
Write-Host ""

artillery run "$PSScriptRoot\load-test.yaml" --output "$PSScriptRoot\load-test-report.json"

# Generate HTML report
Write-Host ""
Write-Host "Generating HTML report..." -ForegroundColor Yellow
artillery report "$PSScriptRoot\load-test-report.json" --output "$PSScriptRoot\load-test-report.html"

Write-Host ""
Write-Host "=== Load Test Complete ===" -ForegroundColor Cyan
Write-Host "Report saved to: $PSScriptRoot\load-test-report.html" -ForegroundColor Cyan
Write-Host ""

# Parse results and check against criteria
$report = Get-Content "$PSScriptRoot\load-test-report.json" | ConvertFrom-Json

$p95Latency = $report.aggregate.latency.p95
$errorRate = ($report.aggregate.errors / $report.aggregate.requestsCompleted) * 100

Write-Host "Performance Summary:" -ForegroundColor Yellow
Write-Host "  P95 Latency: $p95Latency ms" -ForegroundColor Cyan
Write-Host "  Error Rate: $($errorRate.ToString('F2'))%" -ForegroundColor Cyan
Write-Host "  Total Requests: $($report.aggregate.requestsCompleted)" -ForegroundColor Cyan
Write-Host ""

# Check against requirements
$passed = $true

if ($p95Latency -gt 200) {
    Write-Host "✗ FAIL: P95 latency ($p95Latency ms) exceeds 200ms requirement" -ForegroundColor Red
    $passed = $false
} else {
    Write-Host "✓ PASS: P95 latency ($p95Latency ms) is within 200ms requirement" -ForegroundColor Green
}

if ($errorRate -gt 1) {
    Write-Host "✗ FAIL: Error rate ($($errorRate.ToString('F2'))%) exceeds 1% threshold" -ForegroundColor Red
    $passed = $false
} else {
    Write-Host "✓ PASS: Error rate ($($errorRate.ToString('F2'))%) is within 1% threshold" -ForegroundColor Green
}

Write-Host ""
if ($passed) {
    Write-Host "=== All load test criteria passed ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== Load test criteria failed ===" -ForegroundColor Red
    exit 1
}
