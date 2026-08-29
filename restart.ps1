$ErrorActionPreference = "Stop"

Write-Host "Tearing down containers and volumes..."
docker compose down -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Starting fresh (waiting for healthchecks)..."
docker compose up -d --build --wait
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Seeding data..."
docker compose exec api uv run python scripts/seed.py http://elasticsearch:9200
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Ingesting facility location ontology..."
docker compose exec api uv run python -m scripts.ingest_locations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Seeding demo maintenance issues..."
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/maintenance-issues/seed" | Out-Null

Write-Host "Ready."
