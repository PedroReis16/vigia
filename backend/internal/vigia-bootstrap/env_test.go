package bootstrap

import (
	"os"
	"testing"
)

func TestApplyVIGIAAutoInstallEnv(t *testing.T) {
	t.Cleanup(func() { _ = os.Unsetenv("VIGIA_AUTO_INSTALL") })

	cfg := Config{AutoInstall: true}
	_ = os.Setenv("VIGIA_AUTO_INSTALL", "0")
	ApplyVIGIAAutoInstallEnv(&cfg)
	if cfg.AutoInstall {
		t.Fatal("expected false")
	}

	cfg.AutoInstall = false
	_ = os.Setenv("VIGIA_AUTO_INSTALL", "yes")
	ApplyVIGIAAutoInstallEnv(&cfg)
	if !cfg.AutoInstall {
		t.Fatal("expected true")
	}

	_ = os.Unsetenv("VIGIA_AUTO_INSTALL")
	cfg.AutoInstall = true
	ApplyVIGIAAutoInstallEnv(&cfg)
	if !cfg.AutoInstall {
		t.Fatal("unset env must not change cfg")
	}
}
