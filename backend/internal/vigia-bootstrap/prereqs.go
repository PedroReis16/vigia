package bootstrap

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"
)

// EnsurePrerequisites verifica docker e docker compose v2.
func EnsurePrerequisites(ctx context.Context, cfg Config) error {
	if err := requireCommand(ctx, "docker", "--version"); err != nil {
		if cfg.AutoInstall {
			if err2 := tryInstallDocker(ctx); err2 != nil {
				return fmt.Errorf("docker ausente e instalação automática falhou: %w (original: %v)", err2, err)
			}
			if err := requireCommand(ctx, "docker", "--version"); err != nil {
				return err
			}
		} else {
			return fmt.Errorf("%w\n  instale Docker e tente de novo (ou use --auto-install onde suportado)", err)
		}
	}

	if err := requireCommand(ctx, "docker", "compose", "version"); err != nil {
		if cfg.AutoInstall && runtime.GOOS == "linux" {
			if err2 := tryInstallDockerComposePluginLinux(ctx); err2 != nil {
				return fmt.Errorf("docker compose ausente: %w (tentativa plugin: %v)", err, err2)
			}
			if err := requireCommand(ctx, "docker", "compose", "version"); err != nil {
				return err
			}
		} else {
			return fmt.Errorf("%w\n  é necessário o plugin 'docker compose' (v2)", err)
		}
	}

	EnsureDockerGroupForLoginUser(ctx, cfg)
	return nil
}

func requireCommand(ctx context.Context, name string, args ...string) error {
	ctx, cancel := context.WithTimeout(ctx, 2*time.Minute)
	defer cancel()

	cmd := exec.CommandContext(ctx, name, args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s %s: %w (%s)", name, strings.Join(args, " "), err, strings.TrimSpace(string(out)))
	}
	return nil
}

func tryInstallDocker(ctx context.Context) error {
	switch runtime.GOOS {
	case "darwin":
		return requireCommand(ctx, "brew", "install", "--cask", "docker")
	case "linux":
		return installDockerLinux(ctx)
	default:
		return fmt.Errorf("instalação automática não suportada em %s", runtime.GOOS)
	}
}

// installDockerLinux usa o script oficial get.docker.com (Docker Inc.), suporta ARM64 e várias distros.
func installDockerLinux(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 25*time.Minute)
	defer cancel()
	script := `
set -e
export DEBIAN_FRONTEND=noninteractive
if ! command -v curl >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y -qq curl ca-certificates
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y -q curl ca-certificates
  elif command -v yum >/dev/null 2>&1; then
    yum install -y -q curl ca-certificates
  elif command -v zypper >/dev/null 2>&1; then
    zypper install -y curl ca-certificates
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache curl ca-certificates
  else
    echo "curl is required to install Docker; install curl and retry." >&2
    exit 1
  fi
fi
curl -fsSL https://get.docker.com | sh
`
	return runPrivilegedShell(ctx, script)
}

func tryInstallDockerComposePluginLinux(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 10*time.Minute)
	defer cancel()

	if fileExists("/usr/bin/apt-get") {
		script := `
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq docker-compose-plugin
`
		return runPrivilegedShell(ctx, script)
	}

	if fileExists("/usr/bin/dnf") {
		return runPrivilegedShell(ctx, `
set -e
dnf install -y -q docker-compose-plugin
`)
	}

	return fmt.Errorf("instale o plugin docker-compose-plugin para a sua distro (ou reinstale Docker com get.docker.com)")
}

func fileExists(path string) bool {
	st, err := os.Stat(path)
	return err == nil && !st.IsDir()
}

func runPrivilegedShell(ctx context.Context, script string) error {
	var cmd *exec.Cmd
	if os.Geteuid() == 0 {
		cmd = exec.CommandContext(ctx, "sh", "-c", script)
	} else {
		cmd = exec.CommandContext(ctx, "sudo", "sh", "-c", script)
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return err
	}
	return nil
}
