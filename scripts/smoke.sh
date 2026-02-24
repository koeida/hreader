#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

json_assert() {
  local payload="$1"
  local code="$2"
  PAYLOAD="$payload" ASSERT_CODE="$code" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["PAYLOAD"])
code = os.environ["ASSERT_CODE"]
exec(code, {"payload": payload}, {})
PY
}

extract_field() {
  local payload="$1"
  local field="$2"
  PAYLOAD="$payload" FIELD_NAME="$field" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["PAYLOAD"])
print(payload[os.environ["FIELD_NAME"]])
PY
}

echo "[smoke] checking health"
health="$(curl -sS -f "${BASE_URL}/health")"
json_assert "$health" "assert payload['status'] == 'ok', payload"

echo "[smoke] creating user"
user_json="$(curl -sS -f -X POST "${BASE_URL}/v1/users" -H 'Content-Type: application/json' -d '{"display_name":"Smoke User"}')"
user_id="$(extract_field "$user_json" "user_id")"

story='בַּבֹּקֶר יָפֶה. דָּנָה קוֹרֵאת סֵפֶר קָצָר. הַיֶּלֶד רוֹאֶה בַּיִת גָּדוֹל.'
echo "[smoke] creating text"
text_json="$(curl -sS -f -X POST "${BASE_URL}/v1/users/${user_id}/texts" -H 'Content-Type: application/json' -d "{\"title\":\"Smoke Story\",\"content\":\"${story}\"}")"
text_id="$(extract_field "$text_json" "text_id")"

echo "[smoke] renaming text"
rename_json="$(curl -sS -f -X PATCH "${BASE_URL}/v1/users/${user_id}/texts/${text_id}" -H 'Content-Type: application/json' -d '{"title":"Smoke Story Updated"}')"
json_assert "$rename_json" "assert payload['title'] == 'Smoke Story Updated', payload"

echo "[smoke] loading sentence 0"
s0="$(curl -sS -f "${BASE_URL}/v1/users/${user_id}/texts/${text_id}/sentences/0")"
json_assert "$s0" "assert payload['sentence_index'] == 0 and payload['next_sentence_index'] == 1, payload"
normalized_word="$(PAYLOAD="$s0" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ['PAYLOAD'])
assert payload['tokens'], payload
print(payload['tokens'][0]['normalized_word'])
PY
)"
s1="$(curl -sS -f "${BASE_URL}/v1/users/${user_id}/texts/${text_id}/sentences/1")"
json_assert "$s1" "assert payload['sentence_index'] == 1, payload"
s2="$(curl -sS -f "${BASE_URL}/v1/users/${user_id}/texts/${text_id}/sentences/2")"
json_assert "$s2" "assert payload['sentence_index'] == 2 and payload['next_sentence_index'] is None, payload"

echo "[smoke] jump boundary check"
status_out_of_range="$(curl -sS -o /tmp/hreader_smoke_sentence_oor.json -w '%{http_code}' "${BASE_URL}/v1/users/${user_id}/texts/${text_id}/sentences/99")"
if [[ "$status_out_of_range" != "404" ]]; then
  echo "Expected 404 for out-of-range sentence, got ${status_out_of_range}" >&2
  exit 1
fi
json_assert "$(cat /tmp/hreader_smoke_sentence_oor.json)" "assert payload['error']['message'] == 'sentence_not_found', payload"

echo "[smoke] words pagination checks"
words_p1="$(curl -sS -f "${BASE_URL}/v1/users/${user_id}/words?page=1&limit=2")"
json_assert "$words_p1" "assert payload['page'] == 1 and payload['limit'] == 2 and len(payload['items']) == 2 and payload['total'] >= 4, payload"
words_p2="$(curl -sS -f "${BASE_URL}/v1/users/${user_id}/words?page=2&limit=2")"
json_assert "$words_p2" "assert payload['page'] == 2 and len(payload['items']) >= 1, payload"

echo "[smoke] token-state mutation"
update="$(curl -sS -f -X PUT "${BASE_URL}/v1/users/${user_id}/words/${normalized_word}" -H 'Content-Type: application/json' -d '{"state":"known"}')"
json_assert "$update" "assert payload['state'] == 'known', payload"
known="$(curl -sS -f "${BASE_URL}/v1/users/${user_id}/words?state=known")"
WORD="$normalized_word" PAYLOAD="$known" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ['PAYLOAD'])
word = os.environ['WORD']
assert any(item['normalized_word'] == word for item in payload['items']), payload
PY

echo "[smoke] progress verification"
progress="$(curl -sS -f "${BASE_URL}/v1/users/${user_id}/texts/${text_id}/progress")"
json_assert "$progress" "assert payload['known_count'] >= 1, payload"

echo "[smoke] PASS user_id=${user_id} text_id=${text_id} word=${normalized_word}"
