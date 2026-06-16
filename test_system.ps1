Set-Location $PSScriptRoot

$ErrorActionPreference = "Stop"

$env:PGDATABASE = if ($env:PGDATABASE) { $env:PGDATABASE } else { "camera_ai" }
$env:PGUSER = if ($env:PGUSER) { $env:PGUSER } else { "postgres" }

$ApiBase = if ($env:CAMERA_AI_API_BASE) { $env:CAMERA_AI_API_BASE } else { "http://127.0.0.1:8000" }
$Failures = 0

function Test-Step {
    param(
        [string]$Name,
        [scriptblock]$Script
    )

    try {
        $result = & $Script
        Write-Host "[OK] $Name" -ForegroundColor Green
        if ($null -ne $result -and "$result" -ne "") {
            Write-Host "     $result" -ForegroundColor DarkGray
        }
    }
    catch {
        $script:Failures += 1
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        Write-Host "       $($_.Exception.Message)" -ForegroundColor Red
    }
}

Test-Step "Python syntax" {
    python -m py_compile camera_api.py ultralytics\utils\postgres.py
    "camera_api.py and postgres.py compiled"
}

Test-Step "PostgreSQL connection" {
    psql -U $env:PGUSER -d $env:PGDATABASE -t -A -c "SELECT current_database();"
}

Test-Step "Required tables" {
    $count = psql -U $env:PGUSER -d $env:PGDATABASE -t -A -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('detections','detection_events','alerts','alert_rules');"
    if ([int]$count -ne 4) {
        throw "Expected 4 required tables, found $count"
    }
    "detections, detection_events, alerts, alert_rules"
}

Test-Step "Alert rules configured" {
    $count = psql -U $env:PGUSER -d $env:PGDATABASE -t -A -c "SELECT COUNT(*) FROM alert_rules;"
    if ([int]$count -lt 1) {
        throw "No alert rules found"
    }
    "$count rule(s)"
}

Test-Step "API health" {
    $health = Invoke-RestMethod "$ApiBase/health" -TimeoutSec 5
    if ($health.api -ne "ok" -or $health.database -ne "ok") {
        throw "API health is not ok"
    }
    "new_alerts=$($health.new_alerts), active_events=$($health.active_events)"
}

Test-Step "Runtime config endpoint" {
    $config = Invoke-RestMethod "$ApiBase/runtime-config" -TimeoutSec 5
    "database=$($config.database), camera=$($config.camera_id), every_n_frames=$($config.every_n_frames)"
}

Test-Step "Dashboard HTML" {
    $dashboard = Invoke-WebRequest "$ApiBase/dashboard" -TimeoutSec 5 -UseBasicParsing
    if ($dashboard.StatusCode -ne 200) {
        throw "Dashboard returned $($dashboard.StatusCode)"
    }
    foreach ($needle in @("Real-Time Camera AI Dashboard", "Alert Rules", "Runtime Config", "Detections by Object")) {
        if (-not $dashboard.Content.Contains($needle)) {
            throw "Dashboard missing '$needle'"
        }
    }
    "dashboard contains required panels"
}

Test-Step "API data endpoints" {
    $alerts = Invoke-RestMethod "$ApiBase/alerts" -TimeoutSec 5
    $rules = Invoke-RestMethod "$ApiBase/alert-rules" -TimeoutSec 5
    $events = Invoke-RestMethod "$ApiBase/events?limit=5" -TimeoutSec 5
    "alerts=$($alerts.Count), rules=$($rules.Count), events=$($events.Count)"
}

Test-Step "Recent detections query" {
    $count = psql -U $env:PGUSER -d $env:PGDATABASE -t -A -c "SELECT COUNT(*) FROM detections WHERE created_at >= NOW() - INTERVAL '10 minutes';"
    "$count detection(s) in last 10 minutes"
}

if ($Failures -gt 0) {
    Write-Host ""
    Write-Host "System test failed: $Failures check(s) failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "System test passed." -ForegroundColor Green
