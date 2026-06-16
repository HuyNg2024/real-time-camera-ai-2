Set-Location $PSScriptRoot

Write-Host "Installing Python dependencies..."
python -m pip install -e .
python -m pip install fastapi uvicorn psycopg2-binary opencv-python lap

Write-Host "Preparing PostgreSQL database..."
$env:PGDATABASE = "camera_ai"
$env:PGUSER = "postgres"
Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue

$databaseExists = psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'camera_ai'"
if ($databaseExists.Trim() -ne "1") {
    createdb -U postgres camera_ai
    Write-Host "Created database camera_ai"
} else {
    Write-Host "Database camera_ai already exists"
}

psql -U postgres -d camera_ai -f sql/schema.sql

Write-Host ""
Write-Host "Setup complete."
Write-Host "Start API with:  .\run_api.ps1"
Write-Host "Start YOLO with: .\run_yolo.ps1"
Write-Host "Dashboard:       http://127.0.0.1:8000/dashboard"
