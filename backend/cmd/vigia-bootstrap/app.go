package main

import (
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"

	vigiabootstrap "vigia/internal/vigia-bootstrap"
	"vigia/pkg/logger"

	"github.com/spf13/cobra"
	"go.uber.org/zap"
)

func Execute() error {
	return rootCmd.Execute()
}

var rootCmd = &cobra.Command{
	Use:           "vigia-bootstrap",
	Short:         "Serviço que observa imagens Docker Compose e aplica atualizações",
	SilenceUsage:  true,
	SilenceErrors: true,
	RunE:          runDaemon,
}

var installCmd = &cobra.Command{
	Use:   "install-service",
	Short: "Instala e ativa a unit systemd vigia-bootstrap.service",
	RunE:  runInstallService,
}

var uninstallCmd = &cobra.Command{
	Use:   "uninstall-service",
	Short: "Remove o serviço systemd, artefactos em /etc e, por defeito, dados em /var/lib/vigia",
	RunE:  runUninstallService,
}

func init() {
	rootCmd.Flags().String("data-dir", "", "directório para docker-compose.yaml, default.env e logs/")

	installCmd.Flags().String("data-dir", "/var/lib/vigia/bootstrap", "directório de estado (compose + default.env)")
	installCmd.Flags().Bool("now", false, "executar systemctl start após enable")

	uninstallCmd.Flags().Bool("keep-data", false, "não apagar /var/lib/vigia (mantém dados locais)")

	rootCmd.AddCommand(installCmd, uninstallCmd)
}

func runDaemon(cmd *cobra.Command, _ []string) error {
	dataDirFlag, err := cmd.Flags().GetString("data-dir")
	if err != nil {
		return err
	}
	if strings.TrimSpace(dataDirFlag) != "" {
		_ = os.Setenv("VIGIA_BOOTSTRAP_DATA_DIR", filepath.Clean(strings.TrimSpace(dataDirFlag)))
	}

	vigiabootstrap.ApplyBootstrapDataDirFromArgs(os.Args)
	vigiabootstrap.ApplyBootstrapDataDirFromEtcFile()

	if d := strings.TrimSpace(os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR")); d != "" {
		if err := vigiabootstrap.PrepareBootstrapDataDirs(d); err != nil {
			fmt.Fprintf(os.Stderr, "vigia-bootstrap: cannot prepare data directory: %v\n", err)
			return err
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
		return err
	}

	log.Info("Container observer worker started successfully")

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
	<-sigCh
	log.Info("Shutting down vigia-bootstrap")
	return nil
}

func runInstallService(cmd *cobra.Command, _ []string) error {
	dataDir, err := cmd.Flags().GetString("data-dir")
	if err != nil {
		return err
	}
	startNow, err := cmd.Flags().GetBool("now")
	if err != nil {
		return err
	}
	if err := vigiabootstrap.InstallSystemdUnit(dataDir, startNow); err != nil {
		return fmt.Errorf("install-service: %w", err)
	}
	fmt.Printf("Installed %s (data-dir=%s).\n", vigiabootstrap.SystemdUnitInstallPath, dataDir)
	fmt.Println("Try: sudo systemctl status vigia-bootstrap.service")
	return nil
}

func runUninstallService(cmd *cobra.Command, _ []string) error {
	keepData, err := cmd.Flags().GetBool("keep-data")
	if err != nil {
		return err
	}
	if err := vigiabootstrap.UninstallSystemdUnit(keepData); err != nil {
		return fmt.Errorf("uninstall-service: %w", err)
	}
	msg := fmt.Sprintf("Removed systemd unit %s", vigiabootstrap.SystemdUnitInstallPath)
	if !keepData {
		msg += fmt.Sprintf(", %s, and related paths", vigiabootstrap.VarLibVigiaRoot)
	}
	msg += "."
	fmt.Println(msg)
	return nil
}
