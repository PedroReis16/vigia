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

var updateCommand = &cobra.Command{
	Use:   "update",
	Short: "Atualiza o fall-detection para a última versão da API",
	Long:  "Compara a versão instalada com a API; se houver atualização, para o serviço, substitui o binário e inicia novamente.",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Minute)
		defer cancel()

		st, dataDir, err := internal.RequireInstalledFallDetection()
		if err != nil {
			return err
		}

		client, err := internal.RequireAPIClient()
		if err != nil {
			return err
		}

		dto, err := client.FindForUpdates(ctx, st.Version)
		if err != nil {
			return err
		}
		if dto == nil {
			_, _ = fmt.Fprintln(cmd.OutOrStdout(), "Já está na versão mais recente.")
			return nil
		}

		runner := &systemd.Runner{Unit: config.ResolvedSystemdUnit()}
		if err := runner.Stop(ctx); err != nil {
			return fmt.Errorf("systemctl stop: %w", err)
		}

		binPath := st.BinaryPath
		if binPath == "" {
			binPath = install.BinaryPath(dataDir)
		}
		if err := install.DownloadExecutable(ctx, dto.DownloadURL, binPath); err != nil {
			return fmt.Errorf("download: %w", err)
		}

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

		if err := runner.Start(ctx); err != nil {
			return fmt.Errorf("systemctl start: %w", err)
		}

		_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Atualizado para %s\n", ver)
		return nil
	},
}

func init() {
	internal.RootCmd.AddCommand(updateCommand)
}
