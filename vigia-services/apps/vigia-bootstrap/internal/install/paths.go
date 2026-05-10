package install

import (
	"os"
	"path/filepath"
	"strings"
)

const (
	binSubdir  = "bin"
	binaryName = "fall-detection"
	stateFile  = "install.json"
)

// ResolveDataDir returns the absolute data directory from CLI flag, env, or default ~/.vigia.
func ResolveDataDir(flag string) (string, error) {
	v := strings.TrimSpace(flag)
	if v != "" {
		return filepath.Abs(v)
	}
	if v = strings.TrimSpace(os.Getenv("VIGIA_DATA_DIR")); v != "" {
		return filepath.Abs(v)
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return filepath.Abs(filepath.Join(".", ".vigia"))
	}
	return filepath.Join(home, ".vigia"), nil
}

// BinDir returns {dataDir}/bin.
func BinDir(dataDir string) string {
	return filepath.Join(dataDir, binSubdir)
}

// BinaryPath returns the installed executable path.
func BinaryPath(dataDir string) string {
	return filepath.Join(BinDir(dataDir), binaryName)
}

// StatePath returns the path to install.json.
func StatePath(dataDir string) string {
	return filepath.Join(dataDir, stateFile)
}
