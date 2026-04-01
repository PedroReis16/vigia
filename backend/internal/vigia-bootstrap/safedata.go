package bootstrap

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
)

const (
	dataFileBootstrap = "bootstrap.yaml"
	dataFileCompose   = "docker-compose.yaml"
	dataFileDeviceID  = "device-id"
)

func openDataRoot(dataDir string) (*os.Root, error) {
	abs, err := filepath.Abs(filepath.Clean(dataDir))
	if err != nil {
		return nil, err
	}
	return os.OpenRoot(abs)
}

func readDataFile(dataDir, name string) ([]byte, error) {
	switch name {
	case dataFileBootstrap, dataFileCompose, dataFileDeviceID:
	default:
		return nil, fmt.Errorf("ficheiro de dados inválido: %q", name)
	}
	root, err := openDataRoot(dataDir)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	return fs.ReadFile(root.FS(), name)
}

func writeDataFile(dataDir, name string, data []byte, perm fs.FileMode) error {
	switch name {
	case dataFileBootstrap, dataFileCompose, dataFileDeviceID:
	default:
		return fmt.Errorf("ficheiro de dados inválido: %q", name)
	}
	abs, err := filepath.Abs(filepath.Clean(dataDir))
	if err != nil {
		return err
	}
	full := filepath.Join(abs, name)
	if filepath.Base(full) != name {
		return fmt.Errorf("caminho de dados inválido")
	}
	return os.WriteFile(full, data, perm)
}

func statDataFile(dataDir, name string) (fs.FileInfo, error) {
	switch name {
	case dataFileBootstrap, dataFileCompose, dataFileDeviceID:
	default:
		return nil, fmt.Errorf("ficheiro de dados inválido: %q", name)
	}
	root, err := openDataRoot(dataDir)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	return root.Stat(name)
}
