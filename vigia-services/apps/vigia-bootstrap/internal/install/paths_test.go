package install_test

import (
	"path/filepath"
	"strings"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
)

func TestResolveDataDir_flag(t *testing.T) {
	dir := t.TempDir()
	got, err := install.ResolveDataDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	if got != dir {
		t.Fatalf("got %q want %q", got, dir)
	}
}

func TestBinaryPath(t *testing.T) {
	p := install.BinaryPath("/data/vigia")
	if !strings.HasSuffix(p, filepath.Join("bin", "fall-detection")) {
		t.Fatalf("unexpected path %q", p)
	}
}

func TestBinDir(t *testing.T) {
	got := install.BinDir("/var/lib/v")
	want := filepath.Join("/var/lib/v", "bin")
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}

func TestStatePath(t *testing.T) {
	got := install.StatePath("/data/x")
	want := filepath.Join("/data/x", "install.json")
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}

func TestResolveDataDir_trimSpaces(t *testing.T) {
	dir := t.TempDir()
	got, err := install.ResolveDataDir("  " + dir + "  ")
	if err != nil {
		t.Fatal(err)
	}
	if got != dir {
		t.Fatalf("got %q want %q", got, dir)
	}
}

func TestResolveDataDir_env(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("VIGIA_DATA_DIR", dir)
	got, err := install.ResolveDataDir("")
	if err != nil {
		t.Fatal(err)
	}
	if got != dir {
		t.Fatalf("got %q want %q", got, dir)
	}
}

func TestResolveDataDir_defaultUsesHome(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("VIGIA_DATA_DIR", "")
	got, err := install.ResolveDataDir("")
	if err != nil {
		t.Fatal(err)
	}
	want := filepath.Join(home, ".vigia")
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
}
