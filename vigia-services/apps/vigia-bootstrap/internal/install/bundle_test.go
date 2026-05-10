package install_test

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
)

func TestInstallFallDetectionBundle_minimalTarball(t *testing.T) {
	dir := t.TempDir()
	tgz := minimalFallDetectionTarGz(t)

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(tgz)
	}))
	t.Cleanup(srv.Close)

	ctx := context.Background()
	if err := install.InstallFallDetectionBundle(ctx, srv.URL, dir); err != nil {
		t.Fatal(err)
	}

	bin := install.BinaryPath(dir)
	b, err := os.ReadFile(bin)
	if err != nil {
		t.Fatal(err)
	}
	if string(b) != "#!/bin/sh\ntrue\n" {
		t.Fatalf("unexpected payload %q", string(b))
	}
}

func TestEffectiveBinaryPath_prefersLegacyWhenPresent(t *testing.T) {
	dir := t.TempDir()
	legacy := install.LegacyBinaryPath(dir)
	if err := os.MkdirAll(filepath.Dir(legacy), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(legacy, []byte{0}, 0o755); err != nil {
		t.Fatal(err)
	}
	st := &install.State{Version: "1", BinaryPath: legacy}
	got, err := install.EffectiveBinaryPath(st, dir)
	if err != nil {
		t.Fatal(err)
	}
	if got != legacy {
		t.Fatalf("got %q want %q", got, legacy)
	}
}

func minimalFallDetectionTarGz(t *testing.T) []byte {
	t.Helper()
	var buf bytes.Buffer
	gw := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gw)
	payload := []byte("#!/bin/sh\ntrue\n")
	hdr := &tar.Header{
		Name:     "vigia-fall-detection-linux-arm64/vigia-fall-detection",
		Mode:     0o755,
		Size:     int64(len(payload)),
		ModTime:  time.Now(),
		Typeflag: tar.TypeReg,
	}
	if err := tw.WriteHeader(hdr); err != nil {
		t.Fatal(err)
	}
	if _, err := tw.Write(payload); err != nil {
		t.Fatal(err)
	}
	if err := tw.Close(); err != nil {
		t.Fatal(err)
	}
	if err := gw.Close(); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}
