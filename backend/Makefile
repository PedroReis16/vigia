.PHONY: api bootstrap integration test-bootstrap build-bootstrap

api:
	go run ./cmd/vigia-api/main.go

stream:
	go run ./cmd/vigia-stream/main.go

bootstrap:
	go run ./cmd/vigia-bootstrap

integration:
	go run ./cmd/vigia-integration/main.go

test-bootstrap:
	go test ./internal/vigia-bootstrap/...

build-bootstrap:
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o vigia-bootstrap ./cmd/vigia-bootstrap