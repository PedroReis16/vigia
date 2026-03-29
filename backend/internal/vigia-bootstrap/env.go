package bootstrap

import (
	"os"
	"strings"
)

// ApplyVIGIAAutoInstallEnv aplica VIGIA_AUTO_INSTALL ao cfg quando a variável está definida.
// Valores reconhecidos como true: 1, true, yes, on; como false: 0, false, no, off.
func ApplyVIGIAAutoInstallEnv(cfg *Config) {
	v := strings.TrimSpace(os.Getenv("VIGIA_AUTO_INSTALL"))
	if v == "" {
		return
	}
	switch strings.ToLower(v) {
	case "1", "true", "yes", "on":
		cfg.AutoInstall = true
	case "0", "false", "no", "off":
		cfg.AutoInstall = false
	}
}
