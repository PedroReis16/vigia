package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/config"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/systemd"
	"github.com/spf13/cobra"
)

var startAfterInstall bool

var installCommand = &cobra.Command{
	Use:   "install",
	Short: "Instala o bundle fall-detection (tar.gz PyInstaller) a partir da vigia-api",
	Long:  "Consulta a última versão na API, descarrega o tarball onedir, extrai para {data-dir}/fall-detection/ (como no DEPLOY.md) e grava install.json.",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Minute)
		defer cancel()

		client, err := internal.RequireAPIClient()
		if err != nil {
			return err
		}

		dataDir, err := install.ResolveDataDir(config.DataDir)
		if err != nil {
			return err
		}

		dto, err := client.FindForUpdates(ctx, "")
		if err != nil {
			return err
		}
		if dto == nil {
			return fmt.Errorf("nenhuma versão disponível para instalar")
		}

		if err := install.InstallFallDetectionBundle(ctx, dto.DownloadURL, dataDir); err != nil {
			return err
		}

		binPath := install.BinaryPath(dataDir)
		ver := dto.Version
		if ver == "" {
			ver = "unknown"
		}
		if err := install.SaveState(install.StatePath(dataDir), &install.State{
			Version:    ver,
			BinaryPath: binPath,
		}); err != nil {
			return err
		}

		_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Instalado fall-detection %s em %s\n", ver, binPath)

		if startAfterInstall {
			r := &systemd.Runner{Unit: config.ResolvedSystemdUnit()}
			if err := r.EnableNow(ctx); err != nil {
				return fmt.Errorf("systemctl enable --now: %w", err)
			}
			_, _ = fmt.Fprintln(cmd.OutOrStdout(), "Serviço systemd habilitado e iniciado.")
		}
		return nil
	},
}

func init() {
	installCommand.Flags().BoolVar(&startAfterInstall, "start-service", false,
		"Após instalar, executa systemctl enable --now na unit configurada")
	internal.RootCmd.AddCommand(installCommand)
}
