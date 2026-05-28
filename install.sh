#!/usr/bin/env bash
set -euo pipefail

echo "Building and starting services..."

# Prefer classic docker-compose, fall back to 'docker compose' if available
if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DC="docker compose"
else
  echo "ERROR: docker-compose not found."
  echo "On macOS please install Docker Desktop (recommended): https://www.docker.com/products/docker-desktop"
  echo "Or install via Homebrew: brew install --cask docker"
  echo "After installing, start Docker Desktop and re-run this script."
  exit 1
fi

echo "Using: $DC"
$DC up -d --build

echo "Waiting for api to be healthy..."
for i in $(seq 1 30); do
  if curl -s http://localhost:8000/health >/dev/null; then
    echo "api is up"
    break
  fi
  sleep 1
done

echo "Done. Frontend: http://localhost:8080  Backend: http://localhost:8000"
