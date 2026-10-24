#!/bin/sh
set -eu

echo "[entrypoint] Starting container entrypoint"

# Rebuild the frontend at startup so plugin components mounted into src/plugins are
# picked up - Vite's manifest glob resolves at build time, so a mounted plugin is
# invisible until the bundle is regenerated.
#
# Dependencies are baked into the image from the committed lockfile, so this needs no
# registry access and cannot drift between boots. Vite is invoked directly rather than
# through `yarn build` to skip the tsc gate: a type error in a third-party plugin must
# not stop the server from starting. If the build fails for any reason we fall back to
# the bundle shipped with the image rather than crash-looping with no frontend at all.
if [ -d /app/frontend ]; then
  cd /app/frontend
  echo "[entrypoint] Building frontend"
  if ! ./node_modules/.bin/vite build; then
    echo "[entrypoint] WARNING: frontend build failed - serving the bundle shipped with the image"
    echo "[entrypoint] WARNING: plugin UI components will be missing until the build succeeds"
    rm -rf dist
    cp -r dist.baked dist
  fi
else
  echo "[entrypoint] No frontend source found at /app/frontend, skipping build"
fi

echo "[entrypoint] Starting uvicorn server"
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-9583}"
