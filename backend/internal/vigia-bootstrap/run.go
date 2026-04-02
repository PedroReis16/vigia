package bootstrap

import (
	"context"
	"fmt"
	"log"
	"os"
)

// Run executa pré-requisitos, ficheiros em disco, materializa compose, resolve device-id e workers.
func Run(ctx context.Context, cfg Config) error {
	if err := os.MkdirAll(cfg.DataDir, 0o750); err != nil {
		return fmt.Errorf("criar diretório de dados: %w", err)
	}

	LogSystemdInstallHintIfNeeded(cfg)

	if err := EnsureBootstrapYAML(cfg.BootstrapYAMLPath()); err != nil {
		return fmt.Errorf("bootstrap.yaml: %w", err)
	}

	log.Println("verificando pré-requisitos…")
	if err := EnsurePrerequisites(ctx, cfg); err != nil {
		return fmt.Errorf("pré-requisitos: %w", err)
	}

	if err := MaterializeCompose(cfg); err != nil {
		return fmt.Errorf("compose: %w", err)
	}

	fc, err := LoadFileConfig(cfg.BootstrapYAMLPath())
	if err != nil {
		return fmt.Errorf("carregar bootstrap.yaml: %w", err)
	}

	deviceID, err := ResolveDeviceID(cfg, fc)
	if err != nil {
		return fmt.Errorf("device-id: %w", err)
	}
	log.Printf("device-id ativo: %s", deviceID)

	if err := InitialStackUp(ctx, cfg); err != nil {
		return fmt.Errorf("stack inicial: %w", err)
	}

	jobs := []Job{UpdateJob(cfg)}
	log.Println("iniciando rotinas (atualizações de imagens)…")
	return RunJobs(ctx, jobs)
}
