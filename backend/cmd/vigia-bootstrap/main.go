package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	vigiabootstrap "vigia/internal/vigia-bootstrap"
	"vigia/pkg/logger"

	"go.uber.org/zap"
)

func main() {
	if len(os.Args) >= 2 && os.Args[1] == "install-service" {
		fs := flag.NewFlagSet("install-service", flag.ExitOnError)
		dataDir := fs.String("data-dir", "/var/lib/vigia/bootstrap", "directory for docker-compose.yaml and default.env")
		startNow := fs.Bool("now", false, "systemctl start after enable")
		if err := fs.Parse(os.Args[2:]); err != nil {
			os.Exit(2)
		}
		if err := vigiabootstrap.InstallSystemdUnit(*dataDir, *startNow); err != nil {
			fmt.Fprintf(os.Stderr, "install-service: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Installed %s (data-dir=%s).\n", vigiabootstrap.SystemdUnitInstallPath, *dataDir)
		fmt.Println("Try: sudo systemctl status vigia-bootstrap.service")
		os.Exit(0)
	}

	if len(os.Args) >= 2 && os.Args[1] == "uninstall-service" {
		fs := flag.NewFlagSet("uninstall-service", flag.ExitOnError)
		if err := fs.Parse(os.Args[2:]); err != nil {
			os.Exit(2)
		}
		if err := vigiabootstrap.UninstallSystemdUnit(); err != nil {
			fmt.Fprintf(os.Stderr, "uninstall-service: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Removed systemd unit %s (service stopped and disabled if present).\n", vigiabootstrap.SystemdUnitInstallPath)
		os.Exit(0)
	}

	vigiabootstrap.ApplyBootstrapDataDirFromArgs(os.Args)
	vigiabootstrap.ApplyBootstrapDataDirFromEtcFile()

	if d := strings.TrimSpace(os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR")); d != "" {
		if err := vigiabootstrap.PrepareBootstrapDataDirs(d); err != nil {
			fmt.Fprintf(os.Stderr, "vigia-bootstrap: cannot prepare data directory: %v\n", err)
			os.Exit(1)
		}
		if strings.TrimSpace(os.Getenv("VIGIA_LOG_DIR")) == "" {
			_ = os.Setenv("VIGIA_LOG_DIR", filepath.Join(filepath.Clean(d), "logs"))
		}
	}

	fmt.Fprintf(os.Stderr, "vigia-bootstrap: bootstrap dirs VIGIA_BOOTSTRAP_DATA_DIR=%q VIGIA_LOG_DIR=%q\n",
		os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"), os.Getenv("VIGIA_LOG_DIR"))

	log := logger.NewLogger("vigia-bootstrap")

	defer log.Sync()

	log.Info("Starting vigia-bootstrap")

	worker := vigiabootstrap.NewContainerWorker(log)

	if err := worker.Start(); err != nil {
		log.Error("Failed to start container observer worker", zap.String("error", err.Error()))
		os.Exit(1)
	}

	log.Info("Container observer worker started successfully")

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
	<-sigCh
	log.Info("Shutting down vigia-bootstrap")
}