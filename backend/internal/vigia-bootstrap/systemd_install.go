package bootstrap

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// DefaultSystemdUnitPath é o caminho predefinido do unit escrito por install-service.
const DefaultSystemdUnitPath = "/etc/systemd/system/vigia-bootstrap.service"

// InstallSystemdOptions controla a escrita do unit systemd e os passos posteriores.
type InstallSystemdOptions struct {
	// UnitPath é o caminho do ficheiro .service (omissão: /etc/systemd/system/vigia-bootstrap.service).
	UnitPath string
	// BinaryPath é o executável a usar em ExecStart; vazio usa os.Executable() (com symlinks resolvidos).
	BinaryPath string
	// Enable corre systemctl enable.
	Enable bool
	// StartNow corre systemctl start após instalar.
	StartNow bool
}

// InstallSystemdUnit escreve o unit file, corre daemon-reload e opcionalmente enable/start.
// Requer Linux e efeito root (sudo).
func InstallSystemdUnit(cfg Config, opts InstallSystemdOptions) error {
	if runtime.GOOS != "linux" {
		return fmt.Errorf("install-service só está disponível em Linux")
	}
	if os.Geteuid() != 0 {
		return fmt.Errorf("instalação do unit systemd requer root (use sudo)")
	}

	bin := strings.TrimSpace(opts.BinaryPath)
	if bin == "" {
		ex, err := os.Executable()
		if err != nil {
			return fmt.Errorf("resolver executável: %w", err)
		}
		if resolved, err := filepath.EvalSymlinks(ex); err == nil {
			bin = resolved
		} else {
			bin = ex
		}
	}
	bin, err := filepath.Abs(bin)
	if err != nil {
		return fmt.Errorf("caminho do binário: %w", err)
	}

	dataDir, err := filepath.Abs(cfg.DataDir)
	if err != nil {
		return fmt.Errorf("data-dir: %w", err)
	}

	unitPath := opts.UnitPath
	if unitPath == "" {
		unitPath = DefaultSystemdUnitPath
	}
	unitPath, err = filepath.Abs(unitPath)
	if err != nil {
		return err
	}

	content := renderSystemdUnit(bin, dataDir)
	if err := os.WriteFile(unitPath, []byte(content), 0o600); err != nil {
		return fmt.Errorf("escrever %s: %w", unitPath, err)
	}

	if out, err := exec.Command("systemctl", "daemon-reload").CombinedOutput(); err != nil {
		return fmt.Errorf("systemctl daemon-reload: %w (%s)", err, strings.TrimSpace(string(out)))
	}

	unitName := filepath.Base(unitPath)
	if err := ValidateSystemdUnitFilename(unitName); err != nil {
		return err
	}
	if opts.Enable {
		if out, err := exec.Command("systemctl", "enable", unitName).CombinedOutput(); err != nil { // #nosec G204 -- unitName validado
			return fmt.Errorf("systemctl enable %s: %w (%s)", unitName, err, strings.TrimSpace(string(out)))
		}
	}
	if opts.StartNow {
		if out, err := exec.Command("systemctl", "start", unitName).CombinedOutput(); err != nil { // #nosec G204
			return fmt.Errorf("systemctl start %s: %w (%s)", unitName, err, strings.TrimSpace(string(out)))
		}
	}
	return nil
}

// UninstallSystemdOptions controla a remoção do unit e dados locais.
type UninstallSystemdOptions struct {
	UnitPath  string
	PurgeData bool
	DataDir   string // usado só se PurgeData
}

// UninstallSystemdUnit para e desativa o serviço, remove o ficheiro unit e corre daemon-reload.
// Com PurgeData e DataDir, apaga também o diretório de dados (irreversível). Requer Linux e root.
func UninstallSystemdUnit(opts UninstallSystemdOptions) error {
	if runtime.GOOS != "linux" {
		return fmt.Errorf("uninstall-service só está disponível em Linux")
	}
	if os.Geteuid() != 0 {
		return fmt.Errorf("uninstall-service requer root (use sudo)")
	}

	unitPath := opts.UnitPath
	if unitPath == "" {
		unitPath = DefaultSystemdUnitPath
	}
	var err error
	unitPath, err = filepath.Abs(unitPath)
	if err != nil {
		return err
	}
	unitName := filepath.Base(unitPath)
	if err := ValidateSystemdUnitFilename(unitName); err != nil {
		return err
	}

	_ = exec.Command("systemctl", "stop", unitName).Run() // #nosec G204 -- unitName validado
	_ = exec.Command("systemctl", "disable", unitName).Run() // #nosec G204

	if err := os.Remove(unitPath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("remover %s: %w", unitPath, err)
	}

	if out, err := exec.Command("systemctl", "daemon-reload").CombinedOutput(); err != nil {
		return fmt.Errorf("systemctl daemon-reload: %w (%s)", err, strings.TrimSpace(string(out)))
	}

	if opts.PurgeData && strings.TrimSpace(opts.DataDir) != "" {
		dd, err := filepath.Abs(opts.DataDir)
		if err != nil {
			return err
		}
		if err := os.RemoveAll(dd); err != nil {
			return fmt.Errorf("apagar data-dir %s: %w", dd, err)
		}
	}
	return nil
}

func renderSystemdUnit(binaryPath, dataDir string) string {
	mkdirArg := quoteSystemdWord(dataDir)
	execLine := "ExecStart=" + quoteSystemdArgv(binaryPath, "-data-dir", dataDir)
	var b strings.Builder
	b.WriteString("[Unit]\n")
	b.WriteString("Description=Vigia bootstrap (OTA / Docker compose)\n")
	b.WriteString("After=network-online.target docker.service\n")
	b.WriteString("Wants=network-online.target docker.service\n")
	b.WriteString("\n[Service]\n")
	b.WriteString("Type=simple\n")
	b.WriteString("ExecStartPre=/bin/mkdir -p ")
	b.WriteString(mkdirArg)
	b.WriteString("\n")
	b.WriteString(execLine)
	b.WriteString("\n")
	b.WriteString("Restart=on-failure\n")
	b.WriteString("RestartSec=5\n")
	b.WriteString("User=root\n")
	b.WriteString("\n[Install]\n")
	b.WriteString("WantedBy=multi-user.target\n")
	return b.String()
}

func quoteSystemdArgv(parts ...string) string {
	var b strings.Builder
	for i, p := range parts {
		if i > 0 {
			b.WriteByte(' ')
		}
		b.WriteString(quoteSystemdWord(p))
	}
	return b.String()
}

func quoteSystemdWord(s string) string {
	if s == "" {
		return `""`
	}
	if strings.ContainsAny(s, " \t\n\"'\\") {
		return `"` + strings.ReplaceAll(s, `"`, `\"`) + `"`
	}
	return s
}

// LogSystemdInstallHintIfNeeded avisa quando o processo corre em primeiro plano em Linux
// e o unit systemd ainda não existe (systemctl status falharia com "could not be found").
// Suprimir com VIGIA_NO_SYSTEMD_HINT=1.
func LogSystemdInstallHintIfNeeded(cfg Config) {
	if runtime.GOOS != "linux" {
		return
	}
	if os.Getenv("VIGIA_NO_SYSTEMD_HINT") != "" {
		return
	}
	// Sob systemd, INVOCATION_ID está definido; não sugerir install-service.
	if os.Getenv("INVOCATION_ID") != "" {
		return
	}
	if _, err := os.Stat(DefaultSystemdUnitPath); err == nil {
		return
	}
	log.Printf("dica: ainda não há serviço systemd em %s (este run usa data-dir %q); instalação: sudo vigia-bootstrap install",
		DefaultSystemdUnitPath, cfg.DataDir)
}
