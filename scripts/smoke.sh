#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

health="$(curl -sS "${BASE_URL}/health")"
echo "health: ${health}"

user_json="$(curl -sS -X POST "${BASE_URL}/v1/users" -H 'Content-Type: application/json' -d '{"display_name":"Smoke User"}')"
user_id="$(printf '%s' "$user_json" | sed -n 's/.*"user_id":"\([^"]*\)".*/\1/p')"

echo "user_id: ${user_id}"

story='בַּבֹּקֶר יָפֶה. דָּנָה קוֹרֵאת סֵפֶר קָצָר.'
text_json="$(curl -sS -X POST "${BASE_URL}/v1/users/${user_id}/texts" -H 'Content-Type: application/json' -d "{\"title\":\"Smoke Story\",\"content\":\"${story}\"}")"
text_id="$(printf '%s' "$text_json" | sed -n 's/.*"text_id":"\([^"]*\)".*/\1/p')"

echo "text_id: ${text_id}"

sentence="$(curl -sS "${BASE_URL}/v1/users/${user_id}/texts/${text_id}/sentences/0")"
echo "sentence0: ${sentence}"

words="$(curl -sS "${BASE_URL}/v1/users/${user_id}/words")"
echo "words: ${words}"

progress="$(curl -sS "${BASE_URL}/v1/users/${user_id}/texts/${text_id}/progress")"
echo "progress: ${progress}"
