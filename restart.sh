#!/usr/bin/env bash
set -e

echo "Tearing down containers and volumes..."
docker compose down -v

echo "Starting fresh (waiting for healthchecks)..."
docker compose up -d --build --wait

echo "Seeding data..."
docker compose exec api uv run python scripts/seed.py http://elasticsearch:9200

echo "Ingesting facility location ontology..."
docker compose exec api uv run python -m scripts.ingest_locations

echo "Ready."
