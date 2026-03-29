# Build the Go application
FROM golang:1.26.1-alpine AS builder

# Set the working directory in the container
WORKDIR /app

# Copy the go.mod and go.sum files to the container
COPY backend/go.mod backend/go.sum ./
RUN go mod download

# Copy module sources (module root is backend/, not repo root)
COPY backend/ ./

# Production build: optimized binary, strip debug/symbol tables, reproducible paths
# (Go has no separate "Release" profile; this is the usual container pattern.)
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o vigia-api .

# Use a minimal base image like 'alpine:latest' or 'scratch' for the smallest possible size
FROM alpine:latest

# Refresh Alpine packages (e.g. zlib CVE-2026-22184 fixed in 1.3.2-r0+)
RUN apk update && apk upgrade --no-cache

# Set the working directory in the container
WORKDIR /root/

# Copy the binary from the builder stage
COPY --from=builder /app/vigia-api .

# Expose the port the app will run on
EXPOSE 8000

# Set the entrypoint to the binary
CMD ["./vigia-api"]