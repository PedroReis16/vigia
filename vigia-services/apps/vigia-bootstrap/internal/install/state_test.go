package install_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
)

func TestLoadState_missing(t *testing.T) {
	st, err := install.LoadState(filepath.Join(t.TempDir(), "install.json"))
	if err != nil {
		t.Fatal(err)
	}
	if st != nil {
		t.Fatalf("want nil, got %+v", st)
	}
}

func TestLoadState_invalidJSON(t *testing.T) {
	path := filepath.Join(t.TempDir(), "install.json")
	if err := os.WriteFile(path, []byte(`{`), 0o644); err != nil {
		t.Fatal(err)
	}
	_, err := install.LoadState(path)
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestSaveState_roundTrip(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "install.json")
	want := &install.State{Version: "1.2.3", BinaryPath: filepath.Join(dir, "bin", "fall-detection")}
	if err := install.SaveState(path, want); err != nil {
		t.Fatal(err)
	}
	got, err := install.LoadState(path)
	if err != nil {
		t.Fatal(err)
	}
	if got.Version != want.Version || got.BinaryPath != want.BinaryPath {
		t.Fatalf("got %+v want %+v", got, want)
	}
}

func TestSaveState_nil(t *testing.T) {
	err := install.SaveState(filepath.Join(t.TempDir(), "install.json"), nil)
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestLoadState_notARegularFile(t *testing.T) {
	dir := t.TempDir()
	_, err := install.LoadState(dir)
	if err == nil {
		t.Fatal("expected error when path is a directory")
	}
}
