#!/usr/bin/env bash
set -e

echo "Tearing down containers and volumes..."
docker compose down -v

echo "Starting fresh (waiting for healthchecks)..."
docker compose up -d --wait

echo "Seeding data..."
docker compose exec api uv run python scripts/seed.py http://elasticsearch:9200

echo "Ready."
