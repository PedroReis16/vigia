package logger

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCreateFilePathVIGIALogDir(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("VIGIA_LOG_DIR", tmp)

	p := createFilePath("myproj")
	wantDir := filepath.Join(tmp, "myproj")
	wantFile := filepath.Join(wantDir, "myproj.log")
	if p != wantFile {
		t.Fatalf("path = %q want %q", p, wantFile)
	}
	st, err := os.Stat(wantDir)
	if err != nil || !st.IsDir() {
		t.Fatalf("expected parent dir: %v", err)
	}
}

func TestCreateFilePathDefaultUnderHome(t *testing.T) {
	t.Setenv("VIGIA_LOG_DIR", "")
	home := t.TempDir()
	t.Setenv("HOME", home)

	p := createFilePath("x")
	if !strings.HasPrefix(p, home) {
		t.Fatalf("expected under HOME: %s", p)
	}
	if !strings.HasSuffix(p, filepath.Join("vigia", "logs", "x", "x.log")) {
		t.Fatalf("unexpected path: %s", p)
	}
	parent := filepath.Dir(p)
	if st, err := os.Stat(parent); err != nil || !st.IsDir() {
		t.Fatalf("parent dir: %v %v", err, st)
	}
}
