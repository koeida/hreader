#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATUS_FILE="${1:-${ROOT_DIR}/status.md}"
SCHEMA_FILE="${ROOT_DIR}/scripts/autopilot_status_schema.json"
MAX_ITERS="${MAX_ITERS:-200}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"

if [[ ! -f "${STATUS_FILE}" ]]; then
  echo "status file not found: ${STATUS_FILE}" >&2
  exit 1
fi

if [[ ! -f "${SCHEMA_FILE}" ]]; then
  echo "schema file not found: ${SCHEMA_FILE}" >&2
  exit 1
fi

run_once() {
  local result_file
  result_file="$(mktemp)"

  cat <<PROMPT | codex exec \
    --cd "${ROOT_DIR}" \
    --skip-git-repo-check \
    --dangerously-bypass-approvals-and-sandbox \
    --output-schema "${SCHEMA_FILE}" \
    --output-last-message "${result_file}" \
    -
You are in an automated ralph loop for this repository.

Primary file: ${STATUS_FILE}

Do all of the following in this run:
1) Read ${STATUS_FILE}.
2) Choose the highest-leverage next chunk toward completion, including eventual UI completion.
3) Implement code and tests/docs as needed.
4) Run validations relevant to your changes.
5) Update ${STATUS_FILE} with fresh progress, remaining work, and next goals.

Only return JSON matching the provided output schema.
Set done_code="TOTALLY_DONE" only when the full project is truly complete end-to-end.
Otherwise set done_code="CONTINUE".
PROMPT

  local raw done_code
  raw="$(cat "${result_file}")"
  rm -f "${result_file}"

  echo "autopilot_result: ${raw}"

  done_code="$(printf '%s' "${raw}" | tr -d '\n' | sed -n 's/.*"done_code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
  if [[ -z "${done_code}" ]]; then
    echo "failed to parse done_code from Codex output" >&2
    exit 2
  fi

  if [[ "${done_code}" == "TOTALLY_DONE" ]]; then
    echo "project marked TOTALLY_DONE"
    exit 0
  fi
}

iter=1
while (( iter <= MAX_ITERS )); do
  echo "=== autopilot iteration ${iter}/${MAX_ITERS} ==="
  run_once
  ((iter++))
  sleep "${SLEEP_SECONDS}"
done

echo "max iterations reached without TOTALLY_DONE" >&2
exit 3
