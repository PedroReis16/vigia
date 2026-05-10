package install

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// State is persisted at install.json under the data directory.
type State struct {
	Version    string `json:"version"`
	BinaryPath string `json:"binary_path"`
}

// LoadState reads install.json. If missing, returns (nil, nil).
func LoadState(path string) (*State, error) {
	if filepath.Base(path) != stateFile {
		return nil, fmt.Errorf("estado: esperado ficheiro %q", stateFile)
	}
	dir := filepath.Dir(path)
	root, err := os.OpenRoot(dir)
	if err != nil {
		return nil, err
	}
	defer root.Close()

	b, err := root.ReadFile(stateFile)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var s State
	if err := json.Unmarshal(b, &s); err != nil {
		return nil, fmt.Errorf("parse install state: %w", err)
	}
	return &s, nil
}

// SaveState writes install.json atomically.
func SaveState(path string, s *State) error {
	if filepath.Base(path) != stateFile {
		return fmt.Errorf("estado: esperado ficheiro %q", stateFile)
	}
	if s == nil {
		return fmt.Errorf("state is nil")
	}
	b, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o750); err != nil {
		return err
	}
	root, err := os.OpenRoot(dir)
	if err != nil {
		return err
	}
	defer root.Close()

	tmp := stateFile + ".tmp"
	if err := root.WriteFile(tmp, b, 0o600); err != nil {
		return err
	}
	return root.Rename(tmp, stateFile)
}
