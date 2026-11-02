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
  # Checked before building rather than after failing: the container may be given any uid
  # (compose `user:`, rootless Docker), and an unwritable tree produces a long vite stack
  # trace that reads like a code fault rather than a permissions one.
  if [ ! -w dist ] || [ ! -w node_modules/.vite-temp ]; then
    echo "[entrypoint] WARNING: /app/frontend is not writable by uid $(id -u):$(id -g) - skipping the rebuild"
    echo "[entrypoint] WARNING: serving the bundle shipped with the image; plugin UI components will be missing"
  elif ! ./node_modules/.bin/vite build; then
    echo "[entrypoint] WARNING: frontend build failed - serving the bundle shipped with the image"
    echo "[entrypoint] WARNING: plugin UI components will be missing until the build succeeds"
    # Guarded because of `set -e` above: if dist cannot be replaced, the fallback must not
    # abort the entrypoint. Exiting here would turn a cosmetic build failure into a restart
    # loop serving nothing, when the bundle already in dist is strictly better than that.
    if rm -rf dist 2>/dev/null; then
      cp -r dist.baked dist || true
    else
      echo "[entrypoint] WARNING: dist is not writable - leaving the image's bundle in place"
    fi
  fi
else
  echo "[entrypoint] No frontend source found at /app/frontend, skipping build"
fi

echo "[entrypoint] Starting uvicorn server"
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-9583}"
