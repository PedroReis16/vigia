#!/bin/sh
# Fired by MediaMTX runOnUnread when a reader (e.g. WebRTC WHEP) disconnects.
# runOnUnDemand does NOT fire for publisher paths without runOnDemand — the device
# publishes RTMP itself after START_STREAMING — so we stop only when no readers remain.
set -eu

: "${VIGIA_API_BASE:?VIGIA_API_BASE is required}"
: "${VIGIA_MEDIAMTX_TOKEN:?VIGIA_MEDIAMTX_TOKEN is required}"

# Grace so a brief WHEP reconnect does not immediately STOP_STREAMING.
sleep "${UNDEMAND_GRACE_SECONDS:-3}"

path_enc=$(printf '%s' "${MTX_PATH}" | sed 's|/|%2F|g')
# Path gone / API error → treat as zero readers (safe to undemand).
readers=$(curl -sf "http://127.0.0.1:9997/v3/paths/get/${path_enc}" \
  | jq '.readers | length' 2>/dev/null || echo 0)

if [ "${readers}" != "0" ]; then
  exit 0
fi

device_id="${G1:-}"
if [ -z "${device_id}" ]; then
  device_id="${MTX_PATH#live/}"
fi

echo "on_unread: no readers left on ${MTX_PATH}; STOP_STREAMING device ${device_id}"

curl -sS -X PATCH \
  "${VIGIA_API_BASE}/vigia/devices/${device_id}/command/undemand" \
  -H "Content-Type: application/json" \
  -H "X-MediaMTX-Token: ${VIGIA_MEDIAMTX_TOKEN}" \
  -d '{"command":"STOP_STREAMING","commandValue":""}'
