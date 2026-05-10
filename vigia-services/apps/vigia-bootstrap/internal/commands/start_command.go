package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/config"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/systemd"
	"github.com/spf13/cobra"
)

var startCommand = &cobra.Command{
	Use:   "start",
	Short: "Inicia o serviço fall-detection (systemd)",
	Long:  "Exige instalação prévia (install.json e binário). Executa systemctl start.",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
		defer cancel()

		if _, _, err := internal.RequireInstalledFallDetection(); err != nil {
			return err
		}

		r := &systemd.Runner{Unit: config.ResolvedSystemdUnit()}
		if err := r.Start(ctx); err != nil {
			return fmt.Errorf("systemctl start: %w", err)
		}
		_, _ = fmt.Fprintln(cmd.OutOrStdout(), "Serviço iniciado.")
		return nil
	},
}

func init() {
	internal.RootCmd.AddCommand(startCommand)
}
