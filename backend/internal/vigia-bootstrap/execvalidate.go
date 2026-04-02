package bootstrap

import (
	"fmt"
	"path/filepath"
	"regexp"
	"strings"
)

var (
	linuxUsernameRe   = regexp.MustCompile(`^[a-z_][a-z0-9_-]{0,31}$`)
	systemdUnitFileRe = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9:@._%-]*\.service$`)
	dockerImageRefRe  = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9@._/:+_-]{0,511}$`)
)

func validateLinuxUsername(name string) error {
	name = strings.TrimSpace(name)
	if !linuxUsernameRe.MatchString(name) {
		return fmt.Errorf("nome de utilizador inválido para usermod")
	}
	return nil
}

// ValidateSystemdUnitFilename rejeita nomes de ficheiro .service fora do padrão seguro (evita injeção em systemctl).
func ValidateSystemdUnitFilename(unitName string) error {
	unitName = strings.TrimSpace(unitName)
	if !systemdUnitFileRe.MatchString(unitName) {
		return fmt.Errorf("nome de unit systemd inválido: %q", unitName)
	}
	return nil
}

func validateDockerImageRef(ref string) error {
	ref = strings.TrimSpace(ref)
	if ref == "" || len(ref) > 512 || !dockerImageRefRe.MatchString(ref) {
		return fmt.Errorf("referência de imagem Docker inválida")
	}
	return nil
}

func assertBootstrapYAMLPath(path string) (dataDir string, err error) {
	if filepath.Base(path) != dataFileBootstrap {
		return "", fmt.Errorf("caminho deve terminar em %s", dataFileBootstrap)
	}
	return filepath.Dir(path), nil
}

func assertComposeYAMLPath(path string) (dataDir string, err error) {
	if filepath.Base(path) != dataFileCompose {
		return "", fmt.Errorf("caminho deve terminar em %s", dataFileCompose)
	}
	return filepath.Dir(path), nil
}

// SanitizeLogString remove quebras de linha de texto externo (saída de comandos, etc.) para logs.
func SanitizeLogString(s string) string {
	s = strings.ReplaceAll(s, "\r", " ")
	return strings.ReplaceAll(s, "\n", " ")
}
