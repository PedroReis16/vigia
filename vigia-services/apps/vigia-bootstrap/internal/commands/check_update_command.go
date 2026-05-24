package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/spf13/cobra"
)

var checkUpdateJSON bool

// CheckUpdateResult is the --json output schema.
type CheckUpdateResult struct {
	UpdateAvailable  bool   `json:"update_available"`
	InstalledVersion string `json:"installed_version"`
	LatestVersion    string `json:"latest_version,omitempty"`
	DownloadURL      string `json:"download_url,omitempty"`
}

var checkUpdateCommand = &cobra.Command{
	Use:   "check-update",
	Short: "Verifica se há nova versão disponível na vigia-api (sem instalar)",
	Long: `Consulta a vigia-api e informa se há uma nova versão do fall-detection.
��til para o fall-detection decidir se deve acionar vigia-bootstrap update.
Use --json para saída estruturada e parse seguro.`,
	RunE: runCheckUpdate,
}

func runCheckUpdate(cmd *cobra.Command, _ []string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	st, _, err := internal.RequireInstalledFallDetection()
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

	result := CheckUpdateResult{
		UpdateAvailable:  dto != nil,
		InstalledVersion: st.Version,
	}
	if dto != nil {
		result.LatestVersion = dto.Version
		result.DownloadURL = dto.DownloadURL
	}

	if checkUpdateJSON {
		enc := json.NewEncoder(cmd.OutOrStdout())
		enc.SetIndent("", "  ")
		return enc.Encode(result)
	}

	if dto == nil {
		_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Versão instalada: %s — sem atualizações disponíveis.\n", st.Version)
	} else {
		_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Atualização disponível: %s → %s\n", st.Version, dto.Version)
	}
	return nil
}

func init() {
	checkUpdateCommand.Flags().BoolVar(&checkUpdateJSON, "json", false, "Saída em JSON estruturado")
	internal.RootCmd.AddCommand(checkUpdateCommand)
}
