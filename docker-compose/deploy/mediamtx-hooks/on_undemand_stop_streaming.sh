#!/bin/sh
# Fired by MediaMTX runOnUnDemand after runOnDemandCloseAfter with no readers left.
set -eu

: "${VIGIA_API_BASE:?VIGIA_API_BASE is required}"
: "${VIGIA_MEDIAMTX_USER:?VIGIA_MEDIAMTX_USER is required}"
: "${VIGIA_MEDIAMTX_PASSWORD:?VIGIA_MEDIAMTX_PASSWORD is required}"

device_id="${G1:-}"
if [ -z "${device_id}" ]; then
  device_id="${MTX_PATH#live/}"
fi

echo "on_undemand: STOP_STREAMING device ${device_id}"

curl -sS -f -X PATCH \
  "${VIGIA_API_BASE}/vigia/devices/${device_id}/command/undemand" \
  -H "Content-Type: application/json" \
  -u "${VIGIA_MEDIAMTX_USER}:${VIGIA_MEDIAMTX_PASSWORD}" \
  -d '{"command":"STOP_STREAMING","commandValue":""}'
