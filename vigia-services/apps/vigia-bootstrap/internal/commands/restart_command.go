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

var restartCommand = &cobra.Command{
	Use:   "restart",
	Short: "Reinicia o serviço fall-detection (systemd)",
	Long:  "Exige instalação prévia. Executa systemctl restart.",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
		defer cancel()

		if _, _, err := internal.RequireInstalledFallDetection(); err != nil {
			return err
		}

		r := &systemd.Runner{Unit: config.ResolvedSystemdUnit()}
		if err := r.Restart(ctx); err != nil {
			return fmt.Errorf("systemctl restart: %w", err)
		}
		_, _ = fmt.Fprintln(cmd.OutOrStdout(), "Serviço reiniciado.")
		return nil
	},
}

func init() {
	internal.RootCmd.AddCommand(restartCommand)
}
