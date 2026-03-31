# Build vigia-stream (WebSocket + TCP ingest) — main package is cmd/vigia-stream, not module root
FROM golang:1.26.1-alpine AS builder

WORKDIR /app

COPY backend/go.mod backend/go.sum ./
RUN go mod download

COPY backend/ ./

RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o vigia-stream ./cmd/vigia-stream

# Use a minimal base image like 'alpine:latest' or 'scratch' for the smallest possible size
FROM alpine:latest

# Refresh Alpine packages (e.g. zlib CVE-2026-22184 fixed in 1.3.2-r0+)
RUN apk update && apk upgrade --no-cache

# Set the working directory in the container
WORKDIR /root/

# Copy the binary from the builder stage
COPY --from=builder /app/vigia-stream .

# 8090: TCP frames from OpenCV/Python; 8091: Gin + /stream WebSocket
EXPOSE 8090 8091

# Set the entrypoint to the binary
CMD ["./vigia-stream"]