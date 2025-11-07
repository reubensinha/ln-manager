#!/bin/sh
set -eu

echo "[entrypoint] Starting container entrypoint"

# Build frontend at container startup so newly installed plugins or dynamic assets
# that were added to the filesystem are included in the build.
if [ -d /app/frontend ]; then
  echo "[entrypoint] Found frontend source at /app/frontend"
  cd /app/frontend

  # Install deps if node_modules doesn't exist or package.json changed
  if [ ! -d node_modules ]; then
    echo "[entrypoint] Installing frontend dependencies"
    npm install --legacy-peer-deps --silent
  else
    echo "[entrypoint] node_modules exists, skipping npm install"
  fi

  echo "[entrypoint] Building frontend"
  npm run build

  # Copy built assets into backend static directory
  echo "[entrypoint] Updating backend static assets"
  rm -rf /app/backend/static || true
  mkdir -p /app/backend/static
  cp -r dist/* /app/backend/static/ || true
else
  echo "[entrypoint] No frontend source found at /app/frontend, skipping build"
fi

echo "[entrypoint] Starting uvicorn server"
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
