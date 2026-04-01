package bootstrap

import (
	"embed"
	"fmt"
	"io/fs"
	"os"
)

//go:embed configs/docker-compose.yaml
var composeFS embed.FS

const embeddedCompose = "configs/docker-compose.yaml"

// MaterializeCompose copia o compose embutido para cfg.ComposePath() se o ficheiro
// ainda não existir ou se cfg.ForceEmbeddedCompose for true.
func MaterializeCompose(cfg Config) error {
	if err := os.MkdirAll(cfg.DataDir, 0o750); err != nil {
		return fmt.Errorf("criar diretório de dados: %w", err)
	}

	path := cfg.ComposePath()
	if !cfg.ForceEmbeddedCompose {
		if _, err := os.Stat(path); err == nil {
			return nil
		} else if !os.IsNotExist(err) {
			return fmt.Errorf("stat compose: %w", err)
		}
	}

	data, err := fs.ReadFile(composeFS, embeddedCompose)
	if err != nil {
		return fmt.Errorf("ler compose embutido: %w", err)
	}

	if err := os.WriteFile(path, data, 0o600); err != nil {
		return fmt.Errorf("gravar %s: %w", path, err)
	}

	return nil
}
