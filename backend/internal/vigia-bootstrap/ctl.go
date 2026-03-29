package bootstrap

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"
)

// PrepareWorkspace cria data-dir, bootstrap.yaml por omissão e compose embutido se em falta.
func PrepareWorkspace(cfg Config) error {
	if err := os.MkdirAll(cfg.DataDir, 0o755); err != nil {
		return fmt.Errorf("data-dir: %w", err)
	}
	if err := EnsureBootstrapYAML(cfg.BootstrapYAMLPath()); err != nil {
		return err
	}
	return MaterializeCompose(cfg)
}

// Doctor imprime diagnóstico para stdout. Não falha se o Docker estiver ausente.
func Doctor(ctx context.Context, cfg Config) {
	_ = os.MkdirAll(cfg.DataDir, 0o755)
	_ = EnsureBootstrapYAML(cfg.BootstrapYAMLPath())

	fmt.Printf("data-dir:        %s\n", cfg.DataDir)
	fmt.Printf("compose:         %s\n", cfg.ComposePath())
	fmt.Printf("bootstrap.yaml:  %s\n", cfg.BootstrapYAMLPath())
	fmt.Printf("device-id file:  %s\n", cfg.DeviceIDFilePath())

	if st, err := os.Stat(cfg.ComposePath()); err != nil {
		fmt.Printf("compose existe:  não (%v)\n", err)
	} else {
		fmt.Printf("compose existe:  sim (%d bytes)\n", st.Size())
	}

	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	if err := requireCommand(ctx, "docker", "--version"); err != nil {
		fmt.Printf("docker:          ERRO %v\n", err)
	} else {
		fmt.Println("docker:          OK")
	}
	if err := requireCommand(ctx, "docker", "compose", "version"); err != nil {
		fmt.Printf("docker compose:  ERRO %v\n", err)
	} else {
		fmt.Println("docker compose:  OK")
	}

	if err := requireCommand(ctx, "docker", "ps"); err != nil {
		fmt.Printf("docker ps (user): ERRO %v\n", err)
		if strings.Contains(strings.ToLower(err.Error()), "permission denied") {
			fmt.Println("  dica: sudo usermod -aG docker $USER && newgrp docker   (ou termine a sessão SSH)")
		}
	} else {
		fmt.Println("docker ps (user): OK")
	}

	fc, err := LoadFileConfig(cfg.BootstrapYAMLPath())
	if err != nil {
		fmt.Printf("bootstrap.yaml:  ERRO %v\n", err)
	} else {
		id, err := ResolveDeviceID(cfg, fc)
		if err != nil {
			fmt.Printf("device-id:       ERRO %v\n", err)
		} else {
			fmt.Printf("device-id:       %s\n", id)
		}
		fmt.Printf("update interval: %s\n", fc.UpdateInterval())
	}
}

// Status executa docker compose ps (e images).
func Status(ctx context.Context, cfg Config) error {
	if err := PrepareWorkspace(cfg); err != nil {
		return err
	}
	out, err := ComposeRun(ctx, cfg.ComposePath(), "ps", "-a")
	if err != nil {
		return err
	}
	fmt.Println(string(out))
	out2, err := ComposeRun(ctx, cfg.ComposePath(), "images")
	if err != nil {
		fmt.Fprintf(os.Stderr, "aviso: docker compose images: %v\n", err)
		return nil
	}
	fmt.Println(string(out2))
	return nil
}

// Start executa docker compose up -d [serviços...].
func Start(ctx context.Context, cfg Config, services []string) error {
	if err := PrepareWorkspace(cfg); err != nil {
		return err
	}
	args := append([]string{"up", "-d"}, services...)
	_, err := ComposeRun(ctx, cfg.ComposePath(), args...)
	return err
}

// Stop executa docker compose stop [serviços...].
func Stop(ctx context.Context, cfg Config, services []string) error {
	if err := PrepareWorkspace(cfg); err != nil {
		return err
	}
	args := append([]string{"stop"}, services...)
	_, err := ComposeRun(ctx, cfg.ComposePath(), args...)
	return err
}

// Restart executa docker compose restart [serviços...].
func Restart(ctx context.Context, cfg Config, services []string) error {
	if err := PrepareWorkspace(cfg); err != nil {
		return err
	}
	args := append([]string{"restart"}, services...)
	_, err := ComposeRun(ctx, cfg.ComposePath(), args...)
	return err
}

// Usage é o texto de ajuda do binário.
const Usage = `vigia-bootstrap — bootstrap OTA / Docker

Copiar só o binário e executá-lo inicia o processo em primeiro plano.

Instalação automática no Linux (Docker + unit systemd + arranque no boot), tipicamente:
  sudo vigia-bootstrap install
  (equivalente a setup + install-service; o -data-dir omisso usa o home do utilizador em sudo, ver documentação)

Uso:
  vigia-bootstrap [flags]
  vigia-bootstrap run [flags]
  (sem subcomando: inicia o daemon; equivalente a "run")

  vigia-bootstrap doctor [flags]
  vigia-bootstrap setup [flags]              # instala/verifica Docker (Ubuntu/macOS); força instalação automática
  vigia-bootstrap install [flags]            # Linux+root: Docker + install-service (enable + start no fim)
  vigia-bootstrap install-service [flags]    # Linux+root: só cria unit systemd (se Docker já existir)
  vigia-bootstrap uninstall-service [flags]   # Linux+root: para, desativa, remove unit; opcional -purge-data
  vigia-bootstrap status|start|stop|restart [flags] [serviços...]

Flags comuns:
  -data-dir string
        diretório de dados (compose, bootstrap.yaml, device-id) (default ~/ .vigia/bootstrap)
  -auto-install (default true em Linux)
        tentar instalar Docker / docker compose em falta (requer sudo/root na primeira instalação)
  -force-embed-compose
        sobrescrever docker-compose.yaml com o template embutido
  -add-docker-user string
        Linux+root: adicionar utilizador ao grupo docker (omissão: SUDO_USER ou VIGIA_DOCKER_USER)

install / install-service — omissão de -data-dir em Linux:
  • sudo (recomendado): home do utilizador em SUDO_USER (ex.: /home/ubuntu/.vigia/bootstrap)
  • sessão root sem sudo: /var/lib/vigia/bootstrap

install-service (só Linux, tipicamente sudo):
  -enable          systemctl enable no boot (default true)
  -now             systemctl start após gravar o unit (default true; -now=false para não iniciar já)
  -unit-path       caminho do ficheiro .service (default /etc/systemd/system/vigia-bootstrap.service)
  -binary          executável no ExecStart (omissão: caminho deste binário)

uninstall-service (só Linux, tipicamente sudo):
  -purge-data      apagar também o data-dir (irreversível; obrigatório passar -data-dir explícito)
  -data-dir        caminho a apagar com -purge-data (ex. /var/lib/vigia/bootstrap)

Variáveis de ambiente:
  VIGIA_DEVICE_ID       identificador do dispositivo (sobrepõe bootstrap.yaml e ficheiro device-id)
  VIGIA_AUTO_INSTALL    se definido, força auto-instalação: 1/true/yes ou 0/false/no (sobrepõe o default em Linux)
  VIGIA_NO_SYSTEMD_HINT suprimir a dica de install-service ao correr em primeiro plano em Linux
  VIGIA_DOCKER_USER     utilizador a adicionar ao grupo docker quando corre como root (alternativa a -add-docker-user)
`

// IsHelpArg indica flags ou palavras-chave de ajuda.
func IsHelpArg(s string) bool {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "-h", "--help", "help":
		return true
	default:
		return false
	}
}
