# Official MediaMTX image is scratch-based (no shell/curl). Hooks need both.
# See: https://mediamtx.org/docs/kickoff/install (custom image with utilities)
FROM bluenviron/mediamtx:1 AS mediamtx

FROM alpine:3.21
# curl: outbound undemand webhook; jq: parse Control API reader count in on_unread hook
RUN apk add --no-cache curl ca-certificates jq
COPY --from=mediamtx /mediamtx /mediamtx
COPY --from=mediamtx /mediamtx.yml /mediamtx.yml
ENTRYPOINT ["/mediamtx"]
