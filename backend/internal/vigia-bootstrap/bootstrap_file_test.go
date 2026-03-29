package bootstrap

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestFileConfig_UpdateInterval(t *testing.T) {
	if d := (FileConfig{}).UpdateInterval(); d != 5*time.Minute {
		t.Fatalf("default: got %v", d)
	}
	if d := (FileConfig{UpdateCheckInterval: "30s"}).UpdateInterval(); d != 30*time.Second {
		t.Fatalf("30s: got %v", d)
	}
	if d := (FileConfig{UpdateCheckInterval: "bogus"}).UpdateInterval(); d != 5*time.Minute {
		t.Fatalf("invalid should fallback: got %v", d)
	}
}

func TestLoadFileConfig_roundtrip(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "bootstrap.yaml")
	content := "update_check_interval: 10m\ndevice_id: test-id\nwatch_images:\n  - alpine:latest\n"
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	fc, err := LoadFileConfig(path)
	if err != nil {
		t.Fatal(err)
	}
	if fc.UpdateCheckInterval != "10m" || fc.DeviceID != "test-id" || len(fc.WatchImages) != 1 {
		t.Fatalf("unexpected: %+v", fc)
	}
	if fc.UpdateInterval() != 10*time.Minute {
		t.Fatalf("interval: %v", fc.UpdateInterval())
	}
}
