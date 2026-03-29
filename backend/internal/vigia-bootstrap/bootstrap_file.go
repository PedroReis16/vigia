package bootstrap

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

const defaultBootstrapYAML = `# Intervalo entre verificações de atualização no registry (ex.: 5m, 1h).
update_check_interval: 5m

# Vazio = usar/generar device-id no disco. Preencha para forçar um GUID (ex.: testes).
device_id: ""

# Imagens extra a observar (além das linhas image: do docker-compose).
watch_images: []
`

// FileConfig lê-se de bootstrap.yaml no DataDir.
type FileConfig struct {
	UpdateCheckInterval string   `yaml:"update_check_interval"`
	DeviceID            string   `yaml:"device_id"`
	WatchImages         []string `yaml:"watch_images"`
}

// UpdateInterval devolve o intervalo configurado ou o padrão 5m.
func (f FileConfig) UpdateInterval() time.Duration {
	if f.UpdateCheckInterval == "" {
		return 5 * time.Minute
	}
	d, err := time.ParseDuration(f.UpdateCheckInterval)
	if err != nil || d <= 0 {
		return 5 * time.Minute
	}
	return d
}

// EnsureBootstrapYAML cria bootstrap.yaml com valores por omissão se não existir.
func EnsureBootstrapYAML(path string) error {
	if _, err := os.Stat(path); err == nil {
		return nil
	} else if !os.IsNotExist(err) {
		return fmt.Errorf("stat bootstrap.yaml: %w", err)
	}

	if err := os.WriteFile(path, []byte(defaultBootstrapYAML), 0o644); err != nil {
		return fmt.Errorf("gravar bootstrap.yaml: %w", err)
	}
	return nil
}

// LoadFileConfig lê bootstrap.yaml; se não existir, devolve valores por omissão.
func LoadFileConfig(path string) (FileConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return FileConfig{}, nil
		}
		return FileConfig{}, fmt.Errorf("ler bootstrap.yaml: %w", err)
	}
	var fc FileConfig
	if err := yaml.Unmarshal(data, &fc); err != nil {
		return FileConfig{}, fmt.Errorf("parse bootstrap.yaml: %w", err)
	}
	return fc, nil
}
