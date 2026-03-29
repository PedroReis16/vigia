package bootstrap

import (
	"context"
	"log"
	"os"
	"os/exec"
	"os/user"
	"runtime"
	"strings"
)

// EnsureDockerGroupForLoginUser adiciona o utilizador alvo ao grupo docker (Linux, efeito root).
// Prioridade: cfg.AddDockerUser, VIGIA_DOCKER_USER, SUDO_USER. Ignora root.
func EnsureDockerGroupForLoginUser(ctx context.Context, cfg Config) {
	if runtime.GOOS != "linux" {
		return
	}
	if os.Geteuid() != 0 {
		return
	}
	u := strings.TrimSpace(cfg.AddDockerUser)
	if u == "" {
		u = strings.TrimSpace(os.Getenv("VIGIA_DOCKER_USER"))
	}
	if u == "" {
		u = strings.TrimSpace(os.Getenv("SUDO_USER"))
	}
	if u == "" || u == "root" {
		return
	}
	if _, err := user.Lookup(u); err != nil {
		log.Printf("aviso: utilizador %q não existe (grupo docker): %v", u, err)
		return
	}
	cmd := exec.CommandContext(ctx, "usermod", "-aG", "docker", u)
	if out, err := cmd.CombinedOutput(); err != nil {
		log.Printf("aviso: usermod -aG docker %s: %v (%s)", u, err, strings.TrimSpace(string(out)))
		return
	}
	log.Printf("utilizador %q adicionado ao grupo docker; para aplicar na sessão SSH atual: newgrp docker (ou termine a sessão e volte a entrar)", u)
}
