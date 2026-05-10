package internal

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/config"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
)

func TestRequireAPIClient_missingURL(t *testing.T) {
	t.Cleanup(resetGlobals)
	config.APIBaseURL = ""
	t.Setenv("VIGIA_API_BASE_URL", "")
	_, err := RequireAPIClient()
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestRequireAPIClient_ok(t *testing.T) {
	t.Cleanup(resetGlobals)
	config.APIBaseURL = "http://localhost:9999"
	c, err := RequireAPIClient()
	if err != nil {
		t.Fatal(err)
	}
	if c.BaseURL != "http://localhost:9999" {
		t.Fatalf("base URL %q", c.BaseURL)
	}
}

func TestRequireInstalledFallDetection_ok(t *testing.T) {
	t.Cleanup(resetGlobals)
	dir := t.TempDir()
	config.DataDir = dir
	binPath := install.BinaryPath(dir)
	if err := os.MkdirAll(filepath.Dir(binPath), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(binPath, []byte{0}, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := install.SaveState(install.StatePath(dir), &install.State{
		Version:    "1.0.0",
		BinaryPath: binPath,
	}); err != nil {
		t.Fatal(err)
	}

	st, gotDir, err := RequireInstalledFallDetection()
	if err != nil {
		t.Fatal(err)
	}
	if gotDir != dir || st.Version != "1.0.0" {
		t.Fatalf("st=%+v dir=%q", st, gotDir)
	}
}

func TestRequireInstalledFallDetection_noInstallJSON(t *testing.T) {
	t.Cleanup(resetGlobals)
	dir := t.TempDir()
	config.DataDir = dir
	_, _, err := RequireInstalledFallDetection()
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestRequireInstalledFallDetection_emptyBinaryPathUsesDefault(t *testing.T) {
	t.Cleanup(resetGlobals)
	dir := t.TempDir()
	config.DataDir = dir
	binPath := install.BinaryPath(dir)
	if err := os.MkdirAll(filepath.Dir(binPath), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(binPath, []byte{0}, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := install.SaveState(install.StatePath(dir), &install.State{
		Version:    "1.0.0",
		BinaryPath: "",
	}); err != nil {
		t.Fatal(err)
	}
	st, _, err := RequireInstalledFallDetection()
	if err != nil {
		t.Fatal(err)
	}
	if st.BinaryPath != "" {
		t.Fatalf("state should still have empty BinaryPath in file; got %+v", st)
	}
}

func TestRequireInstalledFallDetection_missingBinary(t *testing.T) {
	t.Cleanup(resetGlobals)
	dir := t.TempDir()
	config.DataDir = dir
	if err := install.SaveState(install.StatePath(dir), &install.State{
		Version:    "1.0.0",
		BinaryPath: filepath.Join(dir, "bin", "missing"),
	}); err != nil {
		t.Fatal(err)
	}
	_, _, err := RequireInstalledFallDetection()
	if err == nil {
		t.Fatal("expected error")
	}
}

func resetGlobals() {
	config.APIBaseURL = ""
	config.DataDir = ""
	config.SystemdUnit = ""
}
