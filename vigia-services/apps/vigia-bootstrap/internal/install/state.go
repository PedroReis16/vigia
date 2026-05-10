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
	b, err := os.ReadFile(path)
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
	if s == nil {
		return fmt.Errorf("state is nil")
	}
	b, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, b, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}
