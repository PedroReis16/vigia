package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"vigia/internal/vigia-bootstrap"
)

// defaultDataDirForInstallService define o -data-dir omisso de install-service/install.
//
// Com sudo, os.UserHomeDir() costuma ser /root, o que fazia o unit apontar para
// /root/.vigia/bootstrap enquanto o utilizador esperava ~/ .vigia/bootstrap.
// Se SUDO_USER estiver definido, usa-se o home desse utilizador; caso contrário,
// em root puro usa-se /var/lib/vigia/bootstrap (caminho de sistema).
func defaultDataDirForInstallService() string {
	if runtime.GOOS != "linux" {
		return defaultDataDir()
	}
	if os.Geteuid() == 0 {
		su := strings.TrimSpace(os.Getenv("SUDO_USER"))
		if su != "" && su != "root" {
			u, err := user.Lookup(su)
			if err == nil && u.HomeDir != "" {
				return filepath.Join(u.HomeDir, ".vigia", "bootstrap")
			}
		}
		return "/var/lib/vigia/bootstrap"
	}
	return defaultDataDir()
}

type installServiceFlags struct {
	cfg        bootstrap.Config
	unitPath   string
	binaryPath string
	enable     bool
	startNow   bool
}

func parseInstallServiceFlags(args []string) (*installServiceFlags, error) {
	fs := flag.NewFlagSet("install-service", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	dataDir := fs.String("data-dir", defaultDataDirForInstallService(), "diretório de dados (gravado no unit como -data-dir)")
	autoInstall := fs.Bool("auto-install", runtime.GOOS == "linux", "não afeta o unit; só para consistência com outros comandos")
	forceEmbed := fs.Bool("force-embed-compose", false, "sobrescrever compose embutido")
	addDockerUser := fs.String("add-docker-user", "", "Linux+root: adicionar utilizador ao grupo docker (omissão: SUDO_USER ou VIGIA_DOCKER_USER)")
	enable := fs.Bool("enable", true, "systemctl enable (arranque no boot)")
	startNow := fs.Bool("now", true, "systemctl start após instalar (default true; use -now=false para só gravar o unit)")
	unitPath := fs.String("unit-path", bootstrap.DefaultSystemdUnitPath, "caminho do ficheiro .service a criar")
	binaryPath := fs.String("binary", "", "executável em ExecStart (omissão: este binário, via os.Executable)")
	if err := fs.Parse(args); err != nil {
		return nil, err
	}
	cfg := bootstrap.Config{
		DataDir:              *dataDir,
		AutoInstall:          *autoInstall,
		ForceEmbeddedCompose: *forceEmbed,
		AddDockerUser:        *addDockerUser,
	}
	bootstrap.ApplyVIGIAAutoInstallEnv(&cfg)
	return &installServiceFlags{
		cfg:        cfg,
		unitPath:   *unitPath,
		binaryPath: *binaryPath,
		enable:     *enable,
		startNow:   *startNow,
	}, nil
}

func finishInstallService(f *installServiceFlags) error {
	// #nosec G706 -- caminho de configuração administrativa
	log.Printf("install-service: data-dir no unit: %q", f.cfg.DataDir)
	if err := bootstrap.InstallSystemdUnit(f.cfg, bootstrap.InstallSystemdOptions{
		UnitPath:   f.unitPath,
		BinaryPath: f.binaryPath,
		Enable:     f.enable,
		StartNow:   f.startNow,
	}); err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	bootstrap.EnsureDockerGroupForLoginUser(ctx, f.cfg)
	cancel()
	// #nosec G706 -- caminho administrativo
	log.Printf("unit systemd instalado em %q", f.unitPath)
	if f.enable {
		log.Println("habilitado no boot (systemctl enable)")
	}
	if f.startNow {
		log.Println("serviço iniciado (systemctl start)")
		unitName := filepath.Base(f.unitPath)
		if err := bootstrap.ValidateSystemdUnitFilename(unitName); err != nil {
			return err
		}
		// #nosec G702 G204 -- unitName validado por ValidateSystemdUnitFilename; argv separado
		if out, err := exec.Command("systemctl", "is-active", unitName).CombinedOutput(); err != nil {
			// #nosec G706 -- unitName validado; saída sanitizada
			log.Printf("aviso: systemctl is-active %q: %v — %s", unitName, err, bootstrap.SanitizeLogString(string(out)))
		} else {
			// #nosec G706 -- saída de systemctl sanitizada
			log.Printf("estado do serviço: %s", bootstrap.SanitizeLogString(string(out)))
		}
	}
	return nil
}

func runInstallService(args []string) error {
	f, err := parseInstallServiceFlags(args)
	if err != nil {
		os.Exit(2)
	}
	return finishInstallService(f)
}

// runInstallFull instala Docker (se necessário) e de seguida o unit systemd.
func runInstallFull(args []string) error {
	f, err := parseInstallServiceFlags(args)
	if err != nil {
		os.Exit(2)
	}
	f.cfg.AutoInstall = true
	log.Println("install: a verificar / instalar Docker e dependências (pode demorar)…")
	ctx, cancel := context.WithTimeout(context.Background(), 45*time.Minute)
	defer cancel()
	if err := bootstrap.EnsurePrerequisites(ctx, f.cfg); err != nil {
		return fmt.Errorf("pré-requisitos: %w", err)
	}
	log.Println("install: a instalar o serviço systemd…")
	return finishInstallService(f)
}
