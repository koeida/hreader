#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UVICORN_BIN="${UVICORN_BIN:-$ROOT_DIR/.venv/bin/uvicorn}"
HOST="${HOST:-127.0.0.1}"
REQUESTED_PORT="${PORT:-8000}"
PID_FILE="${PID_FILE:-$ROOT_DIR/.hreader-server.pid}"
LOG_FILE="${LOG_FILE:-$ROOT_DIR/.hreader-server.log}"

if [[ ! -x "$UVICORN_BIN" ]]; then
  echo "Expected executable at $UVICORN_BIN. Run 'make venv && make install' first." >&2
  exit 1
fi

kill_pid_if_running() {
  local pid="$1"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
}

# Stop the server we previously started via this script.
if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${old_pid:-}" ]]; then
    kill_pid_if_running "$old_pid"
  fi
  rm -f "$PID_FILE"
fi

# Stop any other hreader uvicorn instances from this repo.
while IFS= read -r line; do
  pid="${line%% *}"
  cmd="${line#* }"
  if [[ -z "$pid" || "$pid" = "$$" ]]; then
    continue
  fi
  if [[ "$cmd" == *"$ROOT_DIR"* || "$cmd" == *"app.main:app"* ]]; then
    kill_pid_if_running "$pid"
  fi
done < <(pgrep -af "uvicorn.*app.main:app" || true)

PORT="$REQUESTED_PORT"
if ss -ltn "( sport = :$PORT )" | tail -n +2 | grep -q .; then
  PORT="$(REQUESTED_PORT="$REQUESTED_PORT" python3 - <<'PY'
import socket
start = int(__import__('os').environ['REQUESTED_PORT'])
for port in range(start, start + 200):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
            print(port)
            break
        except OSError:
            continue
else:
    raise SystemExit("No open port found")
PY
)"
fi

nohup "$UVICORN_BIN" app.main:app --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
NEW_PID="$!"
echo "$NEW_PID" > "$PID_FILE"

BASE_URL="http://$HOST:$PORT"
for _ in $(seq 1 100); do
  if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
    echo "Server started (pid $NEW_PID)."
    echo "Navigate to: $BASE_URL/"
    echo "Log file: $LOG_FILE"

    # Open in default browser if available
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$BASE_URL/" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
      open "$BASE_URL/" >/dev/null 2>&1 &
    fi

    exit 0
  fi
  if ! kill -0 "$NEW_PID" 2>/dev/null; then
    break
  fi
  sleep 0.1
done

echo "Server failed to start. Recent logs:" >&2
tail -n 40 "$LOG_FILE" >&2 || true
exit 1
