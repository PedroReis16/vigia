package bootstrap

import (
	"fmt"
	"os"
	"strings"

	"github.com/google/uuid"
)

const deviceIDEnv = "VIGIA_DEVICE_ID"

// ResolveDeviceID aplica ordem: variável de ambiente > device_id em bootstrap.yaml >
// ficheiro device-id > gerar novo e gravar.
func ResolveDeviceID(cfg Config, fileCfg FileConfig) (string, error) {
	if v := strings.TrimSpace(os.Getenv(deviceIDEnv)); v != "" {
		return v, nil
	}
	if id := strings.TrimSpace(fileCfg.DeviceID); id != "" {
		return id, nil
	}

	path := cfg.DeviceIDFilePath()
	if data, err := os.ReadFile(path); err == nil {
		id := strings.TrimSpace(string(data))
		if id != "" {
			return id, nil
		}
	} else if !os.IsNotExist(err) {
		return "", fmt.Errorf("ler device-id: %w", err)
	}

	id := uuid.NewString()
	if err := os.WriteFile(path, []byte(id+"\n"), 0o600); err != nil {
		return "", fmt.Errorf("gravar device-id: %w", err)
	}
	return id, nil
}
