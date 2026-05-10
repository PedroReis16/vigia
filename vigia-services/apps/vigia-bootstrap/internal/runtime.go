package internal

import (
	"fmt"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/api"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/config"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
)

// RequireAPIClient returns an api.Client using ResolvedAPIBaseURL.
func RequireAPIClient() (*api.Client, error) {
	base := config.ResolvedAPIBaseURL()
	if base == "" {
		return nil, fmt.Errorf("--api-base-url ou VIGIA_API_BASE_URL é obrigatório")
	}
	return api.NewClient(base)
}

// RequireInstalledFallDetection ensures install.json exists and the installed bundle executable is present.
func RequireInstalledFallDetection() (*install.State, string, error) {
	dataDir, err := install.ResolveDataDir(config.DataDir)
	if err != nil {
		return nil, "", err
	}
	statePath := install.StatePath(dataDir)
	st, err := install.LoadState(statePath)
	if err != nil {
		return nil, dataDir, err
	}
	if st == nil {
		return nil, dataDir, fmt.Errorf("fall-detection não está instalado (ausente %s)", statePath)
	}
	if _, err := install.EffectiveBinaryPath(st, dataDir); err != nil {
		return nil, dataDir, err
	}
	return st, dataDir, nil
}
