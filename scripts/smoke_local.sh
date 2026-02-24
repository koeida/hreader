#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Expected Python runtime at $PYTHON_BIN. Run 'make venv && make install' first." >&2
  exit 1
fi

PORT="$("$PYTHON_BIN" - <<'PY'
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1])
sock.close()
PY
)"

TMP_DIR="$(mktemp -d)"
DB_PATH="$TMP_DIR/smoke-local.db"
SERVER_LOG="$TMP_DIR/server.log"
export HREADER_SMOKE_PORT="$PORT"
export HREADER_DB_PATH="$DB_PATH"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "[smoke-local] starting temporary server on 127.0.0.1:${PORT}"
"$PYTHON_BIN" - <<'PY' >"$SERVER_LOG" 2>&1 &
import os
import uvicorn

from app.main import create_app

app = create_app(db_path=os.environ["HREADER_DB_PATH"])
uvicorn.run(app, host="127.0.0.1", port=int(os.environ["HREADER_SMOKE_PORT"]), log_level="error")
PY
SERVER_PID="$!"

"$PYTHON_BIN" - <<'PY'
import os
import time
import urllib.error
import urllib.request

url = f"http://127.0.0.1:{os.environ['HREADER_SMOKE_PORT']}/health"
deadline = time.monotonic() + 20.0
last_error = None

while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(url, timeout=1.0) as resp:
            if resp.status == 200:
                raise SystemExit(0)
    except (OSError, urllib.error.URLError) as exc:
        last_error = exc
    time.sleep(0.1)

print(f"[smoke-local] health check failed for {url}: {last_error}")
raise SystemExit(1)
PY

echo "[smoke-local] running smoke assertions"
BASE_URL="http://127.0.0.1:${PORT}" bash "$ROOT_DIR/scripts/smoke.sh"

echo "[smoke-local] PASS"
