package install_test

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
)

func TestDownloadExecutable_ok(t *testing.T) {
	const payload = "#!/bin/sh\necho ok\n"
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(payload))
	}))
	defer srv.Close()

	dir := t.TempDir()
	dest := filepath.Join(dir, "bin", "fall-detection")
	ctx := context.Background()
	if err := install.DownloadExecutable(ctx, srv.URL, dest); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(dest)
	if err != nil {
		t.Fatal(err)
	}
	if string(b) != payload {
		t.Fatalf("content mismatch")
	}
	fi, err := os.Stat(dest)
	if err != nil {
		t.Fatal(err)
	}
	if fi.Mode()&0o111 == 0 {
		t.Fatal("expected executable bits")
	}
}

func TestDownloadExecutable_nonOK(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer srv.Close()

	dest := filepath.Join(t.TempDir(), "bin", "fall-detection")
	err := install.DownloadExecutable(context.Background(), srv.URL, dest)
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestDownloadExecutable_connectionRefused(t *testing.T) {
	dest := filepath.Join(t.TempDir(), "bin", "fall-detection")
	err := install.DownloadExecutable(context.Background(), "http://127.0.0.1:1/no", dest)
	if err == nil {
		t.Fatal("expected error")
	}
}
