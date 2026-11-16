# Official MediaMTX image is scratch-based (no shell/curl). Hooks need both.
# See: https://mediamtx.org/docs/kickoff/install (custom image with utilities)
FROM bluenviron/mediamtx:1 AS mediamtx

FROM alpine:3.21
# curl: runOnDemand / runOnUnDemand webhooks
RUN apk add --no-cache curl ca-certificates
COPY --from=mediamtx /mediamtx /mediamtx
COPY --from=mediamtx /mediamtx.yml /mediamtx.yml
ENTRYPOINT ["/mediamtx"]
