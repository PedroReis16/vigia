package vigiabootstrap

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// EtcBootstrapDataDirPath is a one-line file written by install-service (directory path only).
// Used when Environment= or argv are not applied so the runtime still finds the data directory.
const EtcBootstrapDataDirPath = "/etc/vigia-bootstrap/data-dir"

// ApplyBootstrapDataDirFromArgs scans argv for -data-dir / --data-dir and sets VIGIA_BOOTSTRAP_DATA_DIR.
// Does not depend on package flag (works even if systemd or an old binary passes flags differently).
func ApplyBootstrapDataDirFromArgs(argv []string) {
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		switch {
		case a == "--data-dir" || a == "-data-dir":
			if i+1 < len(argv) {
				setBootstrapDataDirEnv(strings.TrimSpace(argv[i+1]))
				return
			}
		case strings.HasPrefix(a, "--data-dir="):
			setBootstrapDataDirEnv(strings.TrimPrefix(a, "--data-dir="))
			return
		case strings.HasPrefix(a, "-data-dir="):
			setBootstrapDataDirEnv(strings.TrimPrefix(a, "-data-dir="))
			return
		}
	}
}

func setBootstrapDataDirEnv(raw string) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return
	}
	_ = os.Setenv("VIGIA_BOOTSTRAP_DATA_DIR", filepath.Clean(raw))
}

// ApplyBootstrapDataDirFromEtcFile sets VIGIA_BOOTSTRAP_DATA_DIR from EtcBootstrapDataDirPath if unset.
// Non-fatal on read errors (permission, etc.) so the process can still use Environment= from systemd.
func ApplyBootstrapDataDirFromEtcFile() {
	if strings.TrimSpace(os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR")) != "" {
		return
	}
	b, err := os.ReadFile(EtcBootstrapDataDirPath)
	if err != nil {
		if os.IsNotExist(err) {
			return
		}
		fmt.Fprintf(os.Stderr, "vigia-bootstrap: warning: cannot read %s: %v\n", EtcBootstrapDataDirPath, err)
		return
	}
	dir := strings.TrimSpace(string(b))
	if dir == "" {
		return
	}
	setBootstrapDataDirEnv(dir)
}

// WriteEtcBootstrapDataDir writes the fallback path file (single line).
func WriteEtcBootstrapDataDir(dataDir string) error {
	dataDir = filepath.Clean(strings.TrimSpace(dataDir))
	if dataDir == "" || dataDir == "." {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(EtcBootstrapDataDirPath), 0750); err != nil {
		return err
	}
	return os.WriteFile(EtcBootstrapDataDirPath, []byte(dataDir+"\n"), 0600)
}

// RemoveEtcBootstrapDataDir removes the fallback file (best-effort).
func RemoveEtcBootstrapDataDir() {
	_ = os.Remove(EtcBootstrapDataDirPath)
}
