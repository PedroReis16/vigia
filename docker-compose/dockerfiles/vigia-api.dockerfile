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

# Set the working directory in the container
WORKDIR /root/

# Copy the binary from the builder stage
COPY --from=builder /app/vigia-api .

# Expose the port the app will run on
EXPOSE 8000

# Set the entrypoint to the binary
CMD ["./vigia-api"]