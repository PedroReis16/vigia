package config_test

import (
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/config"
)

func TestResolvedAPIBaseURL_flagPrecedence(t *testing.T) {
	t.Cleanup(resetConfig)
	config.APIBaseURL = "http://api.example/v1/"
	t.Setenv("VIGIA_API_BASE_URL", "http://ignored")
	got := config.ResolvedAPIBaseURL()
	if got != "http://api.example/v1" {
		t.Fatalf("got %q", got)
	}
}

func TestResolvedAPIBaseURL_env(t *testing.T) {
	t.Cleanup(resetConfig)
	config.APIBaseURL = ""
	t.Setenv("VIGIA_API_BASE_URL", "http://from-env/")
	got := config.ResolvedAPIBaseURL()
	if got != "http://from-env" {
		t.Fatalf("got %q", got)
	}
}

func TestResolvedSystemdUnit_flagPrecedence(t *testing.T) {
	t.Cleanup(resetConfig)
	config.SystemdUnit = "my-unit"
	t.Setenv("VIGIA_SYSTEMD_UNIT", "ignored")
	if got := config.ResolvedSystemdUnit(); got != "my-unit" {
		t.Fatalf("got %q", got)
	}
}

func TestResolvedSystemdUnit_env(t *testing.T) {
	t.Cleanup(resetConfig)
	config.SystemdUnit = ""
	t.Setenv("VIGIA_SYSTEMD_UNIT", "from-env")
	if got := config.ResolvedSystemdUnit(); got != "from-env" {
		t.Fatalf("got %q", got)
	}
}

func TestResolvedSystemdUnit_default(t *testing.T) {
	t.Cleanup(resetConfig)
	config.SystemdUnit = ""
	t.Setenv("VIGIA_SYSTEMD_UNIT", "")
	if got := config.ResolvedSystemdUnit(); got != "fall-detection" {
		t.Fatalf("got %q", got)
	}
}

func resetConfig() {
	config.APIBaseURL = ""
	config.DataDir = ""
	config.SystemdUnit = ""
}
