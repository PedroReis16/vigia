#!/bin/sh
# Fired by MediaMTX runOnDemand when the first reader requests live/{deviceId}
# and nobody is publishing yet. The device publishes RTMP itself after START_STREAMING.
set -eu

: "${VIGIA_API_BASE:?VIGIA_API_BASE is required}"
: "${VIGIA_MEDIAMTX_USER:?VIGIA_MEDIAMTX_USER is required}"
: "${VIGIA_MEDIAMTX_PASSWORD:?VIGIA_MEDIAMTX_PASSWORD is required}"

device_id="${G1:-}"
if [ -z "${device_id}" ]; then
  device_id="${MTX_PATH#live/}"
fi

echo "on_demand: START_STREAMING device ${device_id}"

curl -sS -f -X PATCH \
  "${VIGIA_API_BASE}/vigia/devices/${device_id}/command/demand" \
  -H "Content-Type: application/json" \
  -u "${VIGIA_MEDIAMTX_USER}:${VIGIA_MEDIAMTX_PASSWORD}" \
  -d '{"command":"START_STREAMING","commandValue":""}'
