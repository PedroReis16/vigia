package vigiabootstrap

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
)

// SystemdUnitInstallPath is where install-service writes the unit file.
const SystemdUnitInstallPath = "/etc/systemd/system/vigia-bootstrap.service"

// SystemdUnitName is the systemd unit file name (basename).
const SystemdUnitName = "vigia-bootstrap.service"

// systemdDropInWorkdirPath sorts late (zzz-) so it overrides older drop-ins that set WorkingDirectory to a missing path.
const systemdDropInWorkdirPath = "/etc/systemd/system/vigia-bootstrap.service.d/zzz-vigia-bootstrap-workdir.conf"

// VarLibVigiaRoot is the state directory tree removed on uninstall when keepData is false.
const VarLibVigiaRoot = "/var/lib/vigia"

// DropInResetWorkingDirectory returns the fragment that forces a valid CHDIR for systemd.
func DropInResetWorkingDirectory() string {
	return `# Written by vigia-bootstrap install-service: overrides legacy WorkingDirectory= fragments
# that pointed at /var/lib/... before the directory existed (systemd CHDIR runs before ExecStart).
[Service]
WorkingDirectory=/
`
}

// ExecStartLine returns a single systemd ExecStart= line: binary plus --data-dir (so the path is always set even if Environment= is dropped by overrides).
func ExecStartLine(execPath, dataDir string) string {
	dataDir = filepath.Clean(dataDir)
	quoteIfNeeded := func(s string) string {
		if strings.ContainsAny(s, " \t\n\"\\") {
			return strconv.Quote(s)
		}
		return s
	}
	return fmt.Sprintf("%s --data-dir %s", quoteIfNeeded(execPath), quoteIfNeeded(dataDir))
}

// SystemdUnitContent returns the systemd unit file body (for tests and install).
func SystemdUnitContent(dataDir, execPath string) string {
	dataDir = filepath.Clean(dataDir)
	logDir := filepath.Join(dataDir, "logs")
	execLine := ExecStartLine(execPath, dataDir)
	return fmt.Sprintf(`[Unit]
Description=Vigia bootstrap (compose watcher)
After=docker.service network-online.target
Wants=docker.service network-online.target

[Service]
Type=simple
Environment=VIGIA_BOOTSTRAP_DATA_DIR=%s
Environment=VIGIA_LOG_DIR=%s
ExecStart=%s
Restart=on-failure
RestartSec=10
SyslogIdentifier=vigia-bootstrap

[Install]
WantedBy=multi-user.target
`, dataDir, logDir, execLine)
}

// PrepareBootstrapDataDirs creates dataDir and dataDir/logs. Required before logs/compose bootstrap when using a system path (e.g. /var/lib/...).
func PrepareBootstrapDataDirs(dataDir string) error {
	dataDir = filepath.Clean(dataDir)
	if dataDir == "" || dataDir == "." {
		return fmt.Errorf("invalid data directory")
	}
	if err := os.MkdirAll(dataDir, 0750); err != nil {
		return err
	}
	return os.MkdirAll(filepath.Join(dataDir, "logs"), 0750)
}

// InstallSystemdUnit writes the unit file and runs systemctl. Requires root. Linux only.
func InstallSystemdUnit(dataDir string, startNow bool) error {
	if runtime.GOOS != "linux" {
		return fmt.Errorf("install-service is only supported on Linux")
	}
	execPath, err := resolveExecutablePath()
	if err != nil {
		return err
	}
	dataDir = filepath.Clean(dataDir)
	if dataDir == "" || dataDir == "." {
		return fmt.Errorf("invalid data-dir")
	}

	if err := PrepareBootstrapDataDirs(dataDir); err != nil {
		return fmt.Errorf("prepare data-dir: %w", err)
	}

	if err := WriteEtcBootstrapDataDir(dataDir); err != nil {
		return fmt.Errorf("write %s: %w", EtcBootstrapDataDirPath, err)
	}

	unit := SystemdUnitContent(dataDir, execPath)
	if err := os.WriteFile(SystemdUnitInstallPath, []byte(unit), 0600); err != nil {
		return fmt.Errorf("write %s: %w", SystemdUnitInstallPath, err)
	}

	if err := os.MkdirAll(filepath.Dir(systemdDropInWorkdirPath), 0750); err != nil {
		return fmt.Errorf("mkdir drop-in dir: %w", err)
	}
	if err := os.WriteFile(systemdDropInWorkdirPath, []byte(DropInResetWorkingDirectory()), 0600); err != nil {
		return fmt.Errorf("write %s: %w", systemdDropInWorkdirPath, err)
	}

	if out, err := exec.Command("systemctl", "daemon-reload").CombinedOutput(); err != nil {
		return fmt.Errorf("daemon-reload: %w\n%s", err, strings.TrimSpace(string(out)))
	}
	if out, err := exec.Command("systemctl", "enable", SystemdUnitName).CombinedOutput(); err != nil {
		return fmt.Errorf("enable: %w\n%s", err, strings.TrimSpace(string(out)))
	}
	if startNow {
		out, err := exec.Command("systemctl", "start", SystemdUnitName).CombinedOutput()
		if err != nil {
			return fmt.Errorf("start: %w\n%s", err, strings.TrimSpace(string(out)))
		}
	}
	return nil
}

// UninstallSystemdUnit stops the service, disables it, removes the unit file, optional local data under /var/lib/vigia, and daemon-reloads.
// Requires root on typical setups. Linux only. Missing unit file or stopped service is not an error.
func UninstallSystemdUnit(keepData bool) error {
	if runtime.GOOS != "linux" {
		return fmt.Errorf("uninstall-service is only supported on Linux")
	}

	// Stop and disable if the unit exists / was enabled (ignore failures).
	_, _ = exec.Command("systemctl", "disable", "--now", SystemdUnitName).CombinedOutput()

	if err := os.Remove(SystemdUnitInstallPath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("remove %s: %w", SystemdUnitInstallPath, err)
	}

	RemoveEtcBootstrapDataDir()
	removeEtcVigiaBootstrapDirIfEmpty()

	_ = os.Remove(systemdDropInWorkdirPath)
	dropInDir := filepath.Dir(systemdDropInWorkdirPath)
	if entries, err := os.ReadDir(dropInDir); err == nil && len(entries) == 0 {
		_ = os.Remove(dropInDir)
	}

	if !keepData {
		if err := os.RemoveAll(VarLibVigiaRoot); err != nil {
			return fmt.Errorf("remove %s: %w", VarLibVigiaRoot, err)
		}
	}

	out, err := exec.Command("systemctl", "daemon-reload").CombinedOutput()
	if err != nil {
		return fmt.Errorf("daemon-reload: %w\n%s", err, strings.TrimSpace(string(out)))
	}

	_, _ = exec.Command("systemctl", "reset-failed", SystemdUnitName).CombinedOutput()
	return nil
}

func removeEtcVigiaBootstrapDirIfEmpty() {
	dir := filepath.Dir(EtcBootstrapDataDirPath)
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) != 0 {
		return
	}
	_ = os.Remove(dir)
}

func resolveExecutablePath() (string, error) {
	execPath, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("resolve executable: %w", err)
	}
	execPath, err = filepath.EvalSymlinks(execPath)
	if err != nil {
		return "", fmt.Errorf("resolve executable symlink: %w", err)
	}
	return execPath, nil
}
