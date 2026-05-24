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
	Long: `Compara a versão instalada com a API; se houver atualização, realiza a troca atômica
do bundle (tar.gz onedir) com rollback automático em caso de falha:

  1. Detecta nova versão na vigia-api.
  2. Cria backup do bundle atual (rename atômico → fall-detection.bak/).
  3. Para o serviço systemd.
  4. Baixa e extrai o novo bundle.
  5. Atualiza install.json.
  6. Reinicia o serviço.
  7. Em caso de falha nos passos 4–6: restaura o backup e tenta reiniciar.

Para acionar a partir do fall-detection sem bloquear o próprio processo, execute
vigia-bootstrap em nova sessão (Python: subprocess.Popen(..., start_new_session=True)).`,
	RunE: runUpdate,
}

func runUpdate(cmd *cobra.Command, _ []string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Minute)
	defer cancel()

	out := cmd.OutOrStdout()
	errs := cmd.ErrOrStderr()

	st, dataDir, err := internal.RequireInstalledFallDetection()
	if err != nil {
		return err
	}

	client, err := internal.RequireAPIClient()
	if err != nil {
		return err
	}

	_, _ = fmt.Fprintf(out, "Verificando atualizações (versão instalada: %s)...\n", st.Version)
	dto, err := client.FindForUpdates(ctx, st.Version)
	if err != nil {
		return err
	}
	if dto == nil {
		_, _ = fmt.Fprintln(out, "Já está na versão mais recente.")
		return nil
	}

	_, _ = fmt.Fprintf(out, "Nova versão disponível: %s → %s\n", st.Version, dto.Version)

	// Backup atômico: rename fall-detection/ → fall-detection.bak/
	// Realizado ANTES de parar o serviço para minimizar janela de risco.
	_, _ = fmt.Fprintln(out, "Criando backup do bundle atual...")
	if err := install.BackupBundle(dataDir); err != nil {
		return fmt.Errorf("backup: %w", err)
	}

	runner := &systemd.Runner{Unit: config.ResolvedSystemdUnit()}

	_, _ = fmt.Fprintln(out, "Parando serviço...")
	if err := runner.Stop(ctx); err != nil {
		// Serviço não foi parado; backup ainda existe, restaura sem restart.
		install.CleanupBackup(dataDir)
		return fmt.Errorf("systemctl stop: %w", err)
	}

	// A partir daqui qualquer falha aciona rollback + restart.
	_, _ = fmt.Fprintln(out, "Baixando e instalando novo bundle...")
	installErr := install.InstallFallDetectionBundle(ctx, dto.DownloadURL, dataDir)
	if installErr != nil {
		_, _ = fmt.Fprintln(errs, "Falha na instalação — revertendo para versão anterior...")
		if rbErr := install.RestoreBundle(dataDir, st); rbErr != nil {
			_, _ = fmt.Fprintf(errs, "Erro no rollback: %v\n", rbErr)
		} else {
			_, _ = fmt.Fprintf(errs, "Bundle anterior restaurado (%s).\n", st.Version)
			if startErr := runner.Start(ctx); startErr != nil {
				_, _ = fmt.Fprintf(errs, "Serviço não reiniciou após rollback: %v\n", startErr)
			}
		}
		return fmt.Errorf("instalar bundle: %w", installErr)
	}

	ver := dto.Version
	if ver == "" {
		ver = "unknown"
	}
	binPath := install.BinaryPath(dataDir)
	if err := install.SaveState(install.StatePath(dataDir), &install.State{
		Version:    ver,
		BinaryPath: binPath,
	}); err != nil {
		_, _ = fmt.Fprintln(errs, "Falha ao salvar estado — revertendo...")
		if rbErr := install.RestoreBundle(dataDir, st); rbErr != nil {
			_, _ = fmt.Fprintf(errs, "Erro no rollback: %v\n", rbErr)
		} else {
			_ = runner.Start(ctx)
		}
		return fmt.Errorf("salvar install.json: %w", err)
	}

	_, _ = fmt.Fprintln(out, "Iniciando serviço...")
	if startErr := runner.Start(ctx); startErr != nil {
		_, _ = fmt.Fprintf(errs, "Serviço não iniciou após atualização: %v\nRevertendo...\n", startErr)
		if rbErr := install.RestoreBundle(dataDir, st); rbErr != nil {
			_, _ = fmt.Fprintf(errs, "Erro no rollback: %v\n", rbErr)
		} else {
			_, _ = fmt.Fprintf(errs, "Bundle anterior restaurado (%s).\n", st.Version)
			_ = runner.Start(ctx)
		}
		return fmt.Errorf("systemctl start: %w", startErr)
	}

	install.CleanupBackup(dataDir)
	_, _ = fmt.Fprintf(out, "✓ Atualizado para %s\n", ver)
	return nil
}

func init() {
	internal.RootCmd.AddCommand(updateCommand)
}
