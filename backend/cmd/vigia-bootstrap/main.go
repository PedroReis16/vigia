package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"

	"vigia/internal/vigia-bootstrap"
)

func main() {
	log.SetFlags(0)

	args := os.Args[1:]
	if len(args) == 0 {
		exit(runDaemon(configFromFlags([]string{})))
	}

	if bootstrap.IsHelpArg(args[0]) {
		fmt.Print(bootstrap.Usage)
		os.Exit(0)
	}

	// Flags globais sem subcomando equivalem a "run" (útil em unit files).
	if strings.HasPrefix(args[0], "-") {
		exit(runDaemon(configFromFlags(args)))
	}

	switch args[0] {
	case "run":
		exit(runDaemon(configFromFlags(args[1:])))
	case "doctor":
		cfg, _ := parseCommonFlags(args[1:])
		bootstrap.Doctor(context.Background(), cfg)
	case "setup":
		cfg, _ := parseCommonFlags(args[1:])
		exit(runSetup(cfg))
	case "install":
		exit(runInstallFull(args[1:]))
	case "install-service":
		exit(runInstallService(args[1:]))
	case "uninstall-service":
		exit(runUninstallService(args[1:]))
	case "status":
		cfg, _ := parseCommonFlags(args[1:])
		exit(bootstrap.Status(context.Background(), cfg))
	case "start":
		cfg, rest := parseCommonFlags(args[1:])
		exit(bootstrap.Start(context.Background(), cfg, rest))
	case "stop":
		cfg, rest := parseCommonFlags(args[1:])
		exit(bootstrap.Stop(context.Background(), cfg, rest))
	case "restart":
		cfg, rest := parseCommonFlags(args[1:])
		exit(bootstrap.Restart(context.Background(), cfg, rest))
	default:
		// #nosec G706 -- argv do processo; %q escapa conteúdo
		log.Printf("comando desconhecido: %q\n\n", args[0])
		fmt.Print(bootstrap.Usage)
		os.Exit(2)
	}
}

func parseCommonFlags(args []string) (cfg bootstrap.Config, rest []string) {
	fs := flag.NewFlagSet("common", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	dataDir := fs.String("data-dir", defaultDataDir(), "diretório de dados")
	autoInstall := fs.Bool("auto-install", runtime.GOOS == "linux", "instalar dependências em falta (em Linux o default é true; ver VIGIA_AUTO_INSTALL)")
	forceEmbed := fs.Bool("force-embed-compose", false, "sobrescrever compose embutido")
	addDockerUser := fs.String("add-docker-user", "", "Linux+root: adicionar utilizador ao grupo docker (omissão: SUDO_USER ou VIGIA_DOCKER_USER)")
	if err := fs.Parse(args); err != nil {
		os.Exit(2)
	}
	cfg = bootstrap.Config{
		DataDir:              *dataDir,
		AutoInstall:          *autoInstall,
		ForceEmbeddedCompose: *forceEmbed,
		AddDockerUser:        *addDockerUser,
	}
	bootstrap.ApplyVIGIAAutoInstallEnv(&cfg)
	return cfg, fs.Args()
}

func configFromFlags(args []string) bootstrap.Config {
	cfg, _ := parseCommonFlags(args)
	return cfg
}

func runDaemon(cfg bootstrap.Config) error {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	return bootstrap.Run(ctx, cfg)
}

func runSetup(cfg bootstrap.Config) error {
	cfg.AutoInstall = true
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	log.Println("setup: a instalar / verificar Docker…")
	return bootstrap.EnsurePrerequisites(ctx, cfg)
}

func runUninstallService(args []string) error {
	fs := flag.NewFlagSet("uninstall-service", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	unitPath := fs.String("unit-path", bootstrap.DefaultSystemdUnitPath, "ficheiro .service a remover")
	dataDir := fs.String("data-dir", "", "com -purge-data: diretório a apagar (obrigatório; ex. /var/lib/vigia/bootstrap)")
	purge := fs.Bool("purge-data", false, "apagar também o data-dir (irreversível; requer -data-dir)")
	if err := fs.Parse(args); err != nil {
		os.Exit(2)
	}
	if *purge && strings.TrimSpace(*dataDir) == "" {
		return fmt.Errorf("uninstall-service: -purge-data requer -data-dir explícito (evita apagar o diretório errado)")
	}
	if err := bootstrap.UninstallSystemdUnit(bootstrap.UninstallSystemdOptions{
		UnitPath:  *unitPath,
		PurgeData: *purge,
		DataDir:   *dataDir,
	}); err != nil {
		return err
	}
	log.Printf("unit systemd removido (%s)", *unitPath)
	if *purge {
		log.Printf("data-dir apagado: %s", *dataDir)
	}
	return nil
}

func exit(err error) {
	if err != nil {
		log.Fatalf("vigia-bootstrap: %v", err)
	}
}

func defaultDataDir() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return filepath.Join(".", "vigia-data")
	}
	return filepath.Join(home, ".vigia", "bootstrap")
}
