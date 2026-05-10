package internal

import (
	"fmt"
	"os"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/config"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:           "vigia-bootstrap",
	Short:         "Ferramenta de linha de comando do projeto vigia bootstrap",
	Long:          `Ferramenta de linha de comando do projeto vigia bootstrap`,
	SilenceUsage:  true,
	SilenceErrors: true,
	RunE: func(cmd *cobra.Command, args []string) error {
		return cmd.Help()
	},
}

func Execute() error {
	return RootCmd.Execute()
}

func init() {
	RootCmd.SetOut(os.Stdout)
	RootCmd.SetErr(os.Stderr)

	defaultAPI := os.Getenv("VIGIA_API_BASE_URL")
	RootCmd.PersistentFlags().StringVar(&config.APIBaseURL, "api-base-url", defaultAPI,
		"URL base da vigia-api (env VIGIA_API_BASE_URL)")
	RootCmd.PersistentFlags().StringVar(&config.DataDir, "data-dir", "",
		"Raiz Vigia: install.json, pasta fall-detection/ (bundle onedir). Ex.: /opt/vigia (env VIGIA_DATA_DIR; padrão ~/.vigia)")
	RootCmd.PersistentFlags().StringVar(&config.SystemdUnit, "systemd-unit", "",
		"Nome da unit systemd sem .service (env VIGIA_SYSTEMD_UNIT; padrão fall-detection)")

	RootCmd.AddCommand(versionCmd)
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Versão do projeto",
	Long:  "Exibe a versão do projeto",
	Run: func(cmd *cobra.Command, args []string) {
		_, _ = fmt.Fprintln(cmd.OutOrStdout(), "vigia-bootstrap dev")
	},
}
