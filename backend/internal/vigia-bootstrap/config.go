package bootstrap

import (
	"path/filepath"
)

// Config agrupa opções de bootstrap (diretório alvo, flags de comportamento).
type Config struct {
	// DataDir é o diretório onde docker-compose.yaml, bootstrap.yaml e device-id ficam.
	DataDir string

	// AutoInstall tenta instalar dependências faltantes (macOS: brew; Linux: script oficial get.docker.com e plugin compose quando aplicável).
	// Em Linux o binário usa por defeito auto-instalação ativa; desative com -auto-install=false ou VIGIA_AUTO_INSTALL=0.
	AutoInstall bool

	// ForceEmbeddedCompose sobrescreve docker-compose.yaml com o ficheiro embutido mesmo se já existir.
	ForceEmbeddedCompose bool

	// AddDockerUser (Linux, como root) adiciona este utilizador ao grupo docker para usar o socket sem sudo.
	// Se vazio, usa VIGIA_DOCKER_USER ou SUDO_USER (útil com sudo).
	AddDockerUser string
}

// ComposePath retorna o caminho absoluto do ficheiro compose no diretório de dados.
func (c Config) ComposePath() string {
	return filepath.Join(c.DataDir, "docker-compose.yaml")
}

// BootstrapYAMLPath retorna o caminho de bootstrap.yaml.
func (c Config) BootstrapYAMLPath() string {
	return filepath.Join(c.DataDir, "bootstrap.yaml")
}

// DeviceIDFilePath retorna o caminho do ficheiro com o GUID persistido.
func (c Config) DeviceIDFilePath() string {
	return filepath.Join(c.DataDir, "device-id")
}
