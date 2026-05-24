package install

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const (
	appDirName       = "fall-detection"
	bundleBinaryName = "vigia-fall-detection"
	stateFile        = "install.json"
)

// ResolveDataDir returns the absolute data directory from CLI flag, env, or default ~/.vigia.
// For instalação em placa, use tipicamente --data-dir /opt/vigia (raiz Vigia: fall-detection/, install.json).
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

// AppDir returns {dataDir}/fall-detection (bundle PyInstaller onedir).
func AppDir(dataDir string) string {
	return filepath.Join(dataDir, appDirName)
}

// BinaryPath returns the installed executable path (ExecStart do fall-detection.service).
func BinaryPath(dataDir string) string {
	return filepath.Join(AppDir(dataDir), bundleBinaryName)
}

// LegacyBinaryPath is the layout antigo ({dataDir}/bin/fall-detection), antes do tarball onedir.
func LegacyBinaryPath(dataDir string) string {
	return filepath.Join(dataDir, "bin", "fall-detection")
}

// EffectiveBinaryPath resolves the real executable path from install.json and fallbacks (layout atual e legado).
func EffectiveBinaryPath(st *State, dataDir string) (string, error) {
	var candidates []string
	if st != nil && strings.TrimSpace(st.BinaryPath) != "" {
		candidates = append(candidates, st.BinaryPath)
	}
	candidates = append(candidates, BinaryPath(dataDir), LegacyBinaryPath(dataDir))

	seen := make(map[string]bool)
	for _, p := range candidates {
		if p == "" || seen[p] {
			continue
		}
		seen[p] = true
		fi, err := os.Stat(p)
		if err != nil || fi.IsDir() {
			continue
		}
		return p, nil
	}
	return "", fmt.Errorf("binário do fall-detection não encontrado sob %q (corra install ou verifique o caminho em install.json)", dataDir)
}

// StatePath returns the path to install.json.
func StatePath(dataDir string) string {
	return filepath.Join(dataDir, stateFile)
}
