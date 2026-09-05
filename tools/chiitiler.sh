#!/usr/bin/env bash
# Bootstrap and run chiitiler (https://github.com/Kanahiro/chiitiler), the tile
# server tools/thumbnail.py renders through. Clones it into .cache/chiitiler if
# missing, npm installs if node_modules is missing, then runs the tile server
# in the foreground on port 13579 with an in-memory tile cache.
#
# Usage:
#   tools/chiitiler.sh              # run in the foreground (Ctrl-C to stop)
#   tools/chiitiler.sh &            # run in the background of this shell
#   CHIITILER_PORT=3000 tools/chiitiler.sh
#
# Health check once it's up:
#   curl -s http://localhost:13579/health
#
# Stop a backgrounded server from anywhere with:
#   pkill -f "tile-server --port 13579"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_DIR="$ROOT/.cache/chiitiler"
PORT="${CHIITILER_PORT:-13579}"

if [[ ! -d "$CACHE_DIR" ]]; then
    echo "cloning Kanahiro/chiitiler into $CACHE_DIR"
    git clone --depth 1 https://github.com/Kanahiro/chiitiler "$CACHE_DIR"
fi

if [[ ! -d "$CACHE_DIR/node_modules" ]]; then
    echo "installing chiitiler dependencies (npm install)"
    (cd "$CACHE_DIR" && npm install)
fi

echo "starting chiitiler on port $PORT (cache: memory)"
echo "stop with: pkill -f 'tile-server --port $PORT'"
cd "$CACHE_DIR"
exec env CHIITILER_PROCESSES=0 npx tsx src/main.ts tile-server --port "$PORT" --cache memory
