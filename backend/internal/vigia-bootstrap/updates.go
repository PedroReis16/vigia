package bootstrap

import (
	"context"
	"fmt"
	"log"
	"os/exec"
	"strings"
	"time"
)

func mergeImageRefs(fromCompose, extra []string) []string {
	seen := make(map[string]struct{})
	var out []string
	add := func(s string) {
		s = strings.TrimSpace(s)
		if s == "" {
			return
		}
		if _, ok := seen[s]; ok {
			return
		}
		seen[s] = struct{}{}
		out = append(out, s)
	}
	for _, s := range fromCompose {
		add(s)
	}
	for _, s := range extra {
		add(s)
	}
	return out
}

func localRepoDigests(ctx context.Context, imageRef string) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, 2*time.Minute)
	defer cancel()
	cmd := exec.CommandContext(ctx, "docker", "image", "inspect", imageRef, "--format", "{{range .RepoDigests}}{{.}} {{end}}")
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

func digestContained(localDigests, remoteDigest string) bool {
	remoteDigest = strings.TrimPrefix(strings.TrimSpace(remoteDigest), "sha256:")
	if remoteDigest == "" {
		return false
	}
	for _, part := range strings.Fields(localDigests) {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		if strings.Contains(part, remoteDigest) {
			return true
		}
	}
	return false
}

// CheckAndApplyUpdates compara digests no Hub com imagens locais; se necessário faz pull e up -d.
func CheckAndApplyUpdates(ctx context.Context, cfg Config, fc FileConfig) error {
	composePath := cfg.ComposePath()
	fromCompose, err := ImagesFromCompose(composePath)
	if err != nil {
		return fmt.Errorf("imagens do compose: %w", err)
	}
	images := mergeImageRefs(fromCompose, fc.WatchImages)
	if len(images) == 0 {
		return nil
	}

	needPull := false
	for _, img := range images {
		if strings.Contains(img, "@") {
			continue
		}
		remote, err := RegistryManifestDigest(ctx, img)
		if err != nil {
			log.Printf("[updates] registry %q: %v (ignorando esta imagem)", img, err)
			continue
		}
		local, err := localRepoDigests(ctx, img)
		if err != nil || local == "" || !digestContained(local, remote) {
			log.Printf("[updates] nova versão ou imagem em falta: %s (remoto %s)", img, remote)
			needPull = true
			break
		}
	}

	if !needPull {
		return nil
	}

	log.Println("[updates] a executar docker compose pull && up -d …")
	if _, err := ComposeRun(ctx, composePath, "pull"); err != nil {
		return err
	}
	if _, err := ComposeRun(ctx, composePath, "up", "-d"); err != nil {
		return err
	}
	log.Println("[updates] stack atualizado.")
	return nil
}

// InitialStackUp faz pull e up -d uma vez no arranque do daemon quando o compose declara imagens.
// Garante download e subida dos contentores sem depender só do primeiro ciclo do job de updates
// (útil na primeira instalação e após reboot).
func InitialStackUp(ctx context.Context, cfg Config) error {
	composePath := cfg.ComposePath()
	imgs, err := ImagesFromCompose(composePath)
	if err != nil {
		return fmt.Errorf("imagens do compose: %w", err)
	}
	if len(imgs) == 0 {
		log.Println("stack: nenhum serviço com image no compose; a saltar pull/up inicial")
		return nil
	}
	log.Println("stack: pull e up -d inicial (primeiro arranque / arranque do serviço)…")
	if _, err := ComposeRun(ctx, composePath, "pull"); err != nil {
		return fmt.Errorf("compose pull inicial: %w", err)
	}
	if _, err := ComposeRun(ctx, composePath, "up", "-d"); err != nil {
		return fmt.Errorf("compose up inicial: %w", err)
	}
	log.Println("stack: compose aplicado.")
	return nil
}

// UpdateJob devolve um Job que recarrega bootstrap.yaml em cada ciclo e aplica o intervalo configurado.
func UpdateJob(cfg Config) Job {
	bootstrapPath := cfg.BootstrapYAMLPath()
	intervalFn := func() time.Duration {
		fc, err := LoadFileConfig(bootstrapPath)
		if err != nil {
			log.Printf("[updates] ler config: %v", err)
			return 5 * time.Minute
		}
		return fc.UpdateInterval()
	}

	return Job{
		Name:           "updates",
		Interval:       5 * time.Minute,
		IntervalFn:     intervalFn,
		RunImmediately: true,
		Fn: func(ctx context.Context) error {
			fc, err := LoadFileConfig(bootstrapPath)
			if err != nil {
				log.Printf("[updates] %v", err)
				return nil
			}
			if err := CheckAndApplyUpdates(ctx, cfg, fc); err != nil {
				log.Printf("[updates] falha: %v", err)
			}
			return nil
		},
	}
}
