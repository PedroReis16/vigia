.PHONY: help tidy test-all build-all \
	run-api run-bootstrap \
	test-api test-bootstrap test-internal \
	build-api build-bootstrap \
	build-linux-arm64-api build-linux-arm64-bootstrap \
	clean

BIN_DIR := bin
API_DIR := apps/vigia-api
BOOTSTRAP_DIR := apps/vigia-bootstrap
INTERNAL_BOOTSTRAP_DIR := apps/vigia-bootstrap/internal

help:
	@echo "Targets disponiveis:"
	@echo "  run-api | run-bootstrap"
	@echo "  test-api | test-bootstrap | test-internal | test-all"
	@echo "  build-api | build-bootstrap | build-all"
	@echo "  build-linux-arm64-api | build-linux-arm64-bootstrap"
	@echo "  tidy | clean"

tidy:
	@for d in $(API_DIR) pkg/shared $(BOOTSTRAP_DIR); do \
		echo "==> go mod tidy $$d"; \
		(cd $$d && go mod tidy); \
	done
	go work sync

run-api:
	go run ./$(API_DIR)/cmd

run-bootstrap:
	go run ./$(BOOTSTRAP_DIR)

test-api:
	go test ./$(API_DIR)/...

test-bootstrap:
	go test ./$(BOOTSTRAP_DIR)/...

test-internal:
	go test ./$(INTERNAL_BOOTSTRAP_DIR)/...

test-all: test-api test-internal test-bootstrap

build-api:
	@mkdir -p $(BIN_DIR)
	go build -o $(BIN_DIR)/vigia-api ./$(API_DIR)/cmd

build-bootstrap:
	@mkdir -p $(BIN_DIR)
	go build -o $(BIN_DIR)/vigia-bootstrap ./$(BOOTSTRAP_DIR)/cmd

build-all: build-api build-bootstrap

build-linux-arm64-api:
	@mkdir -p $(BIN_DIR)
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o $(BIN_DIR)/vigia-api-linux-arm64 ./$(API_DIR)/cmd

build-linux-arm64-bootstrap:
	@mkdir -p $(BIN_DIR)
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o $(BIN_DIR)/vigia-bootstrap-linux-arm64 ./$(BOOTSTRAP_DIR)/cmd

clean:
	rm -rf $(BIN_DIR)
