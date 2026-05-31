package commands

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	bootroot "github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/config"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/install"
)

func TestCLI_install_endToEnd(t *testing.T) {
	t.Cleanup(resetCLIState)
	srv := newAPIAndArtifactServer(t)
	dir := t.TempDir()

	bootroot.RootCmd.SetOut(io.Discard)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"install", "--api-base-url", srv.URL, "--data-dir", dir})
	if err := bootroot.Execute(); err != nil {
		t.Fatal(err)
	}

	bin := install.BinaryPath(dir)
	if _, err := os.Stat(bin); err != nil {
		t.Fatalf("binary: %v", err)
	}
	st, err := install.LoadState(install.StatePath(dir))
	if err != nil || st == nil || st.Version != "1.0.0" {
		t.Fatalf("state %+v err %v", st, err)
	}
}

func TestCLI_update_noUpdate204(t *testing.T) {
	t.Cleanup(resetCLIState)
	dir := t.TempDir()
	binPath := install.BinaryPath(dir)
	if err := os.MkdirAll(filepath.Dir(binPath), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(binPath, []byte{0}, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := install.SaveState(install.StatePath(dir), &install.State{
		Version:    "9.9.9",
		BinaryPath: binPath,
	}); err != nil {
		t.Fatal(err)
	}

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "find-for-updates") {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)

	out := new(strings.Builder)
	bootroot.RootCmd.SetOut(out)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"update", "--api-base-url", srv.URL, "--data-dir", dir})
	if err := bootroot.Execute(); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(out.String(), "mais recente") {
		t.Fatalf("output %q", out.String())
	}
}

func TestCLI_update_upgradesWithFakeSystemctl(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("requires fake systemctl script")
	}
	t.Cleanup(resetCLIState)

	dir := t.TempDir()
	oldBin := install.BinaryPath(dir)
	if err := os.MkdirAll(filepath.Dir(oldBin), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(oldBin, []byte("old"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := install.SaveState(install.StatePath(dir), &install.State{
		Version:    "1.0.0",
		BinaryPath: oldBin,
	}); err != nil {
		t.Fatal(err)
	}

	artifact := cliMinimalFallDetectionTarGz(t)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		base := "http://" + r.Host
		if strings.Contains(r.URL.Path, "find-for-updates") {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprintf(w, `{"version":"2.0.0","download_url":"%s/artifact"}`, base)
			return
		}
		if r.URL.Path == "/artifact" {
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write(artifact)
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)

	stubDir := t.TempDir()
	stub := filepath.Join(stubDir, "systemctl")
	if err := os.WriteFile(stub, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatal(err)
	}
	oldPath := os.Getenv("PATH")
	t.Cleanup(func() { _ = os.Setenv("PATH", oldPath) })
	_ = os.Setenv("PATH", stubDir+string(os.PathListSeparator)+oldPath)

	bootroot.RootCmd.SetOut(io.Discard)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"update", "--api-base-url", srv.URL, "--data-dir", dir})
	if err := bootroot.Execute(); err != nil {
		t.Fatal(err)
	}

	st, err := install.LoadState(install.StatePath(dir))
	if err != nil || st.Version != "2.0.0" {
		t.Fatalf("state %+v err %v", st, err)
	}
}

func TestCLI_start_notInstalled(t *testing.T) {
	t.Cleanup(resetCLIState)
	dir := t.TempDir()

	bootroot.RootCmd.SetOut(io.Discard)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"start", "--data-dir", dir})
	err := bootroot.Execute()
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestCLI_install_requiresAPIURL(t *testing.T) {
	t.Cleanup(resetCLIState)
	bootroot.RootCmd.SetOut(io.Discard)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"install", "--data-dir", t.TempDir()})
	err := bootroot.Execute()
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestCLI_install_noVersionFromAPI(t *testing.T) {
	t.Cleanup(resetCLIState)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	t.Cleanup(srv.Close)

	bootroot.RootCmd.SetOut(io.Discard)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"install", "--api-base-url", srv.URL, "--data-dir", t.TempDir()})
	err := bootroot.Execute()
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestCLI_install_startServiceWithFakeSystemctl(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("requires fake systemctl script")
	}
	t.Cleanup(resetCLIState)

	stubDir := t.TempDir()
	stub := filepath.Join(stubDir, "systemctl")
	if err := os.WriteFile(stub, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatal(err)
	}
	oldPath := os.Getenv("PATH")
	t.Cleanup(func() { _ = os.Setenv("PATH", oldPath) })
	_ = os.Setenv("PATH", stubDir+string(os.PathListSeparator)+oldPath)

	srv := newAPIAndArtifactServer(t)
	dir := t.TempDir()

	bootroot.RootCmd.SetOut(io.Discard)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"install", "--api-base-url", srv.URL, "--data-dir", dir, "--start-service"})
	if err := bootroot.Execute(); err != nil {
		t.Fatal(err)
	}
}

func newAPIAndArtifactServer(t *testing.T) *httptest.Server {
	t.Helper()
	artifact := cliMinimalFallDetectionTarGz(t)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		base := "http://" + r.Host
		if strings.Contains(r.URL.Path, "/v1/devices/version/find-for-updates") {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprintf(w, `{"version":"1.0.0","download_url":"%s/artifact"}`, base)
			return
		}
		if r.URL.Path == "/artifact" {
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write(artifact)
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)
	return srv
}

func cliMinimalFallDetectionTarGz(t *testing.T) []byte {
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

func resetCLIState() {
	config.APIBaseURL = ""
	config.DataDir = ""
	config.SystemdUnit = ""
	startAfterInstall = false
	checkUpdateJSON = false
	bootroot.RootCmd.SetArgs(nil)
}

func TestCLI_checkUpdate_noUpdate(t *testing.T) {
	t.Cleanup(resetCLIState)
	dir := t.TempDir()
	binPath := install.BinaryPath(dir)
	if err := os.MkdirAll(filepath.Dir(binPath), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(binPath, []byte{0}, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := install.SaveState(install.StatePath(dir), &install.State{
		Version:    "2.0.0",
		BinaryPath: binPath,
	}); err != nil {
		t.Fatal(err)
	}

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "find-for-updates") {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)

	out := new(strings.Builder)
	bootroot.RootCmd.SetOut(out)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"check-update", "--api-base-url", srv.URL, "--data-dir", dir})
	if err := bootroot.Execute(); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(out.String(), "sem atualizações") {
		t.Fatalf("output %q", out.String())
	}
}

func TestCLI_checkUpdate_updateAvailable(t *testing.T) {
	t.Cleanup(resetCLIState)
	dir := t.TempDir()
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

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "find-for-updates") {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprintf(w, `{"version":"2.0.0","download_url":"http://%s/artifact"}`, r.Host)
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)

	out := new(strings.Builder)
	bootroot.RootCmd.SetOut(out)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"check-update", "--api-base-url", srv.URL, "--data-dir", dir})
	if err := bootroot.Execute(); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(out.String(), "2.0.0") {
		t.Fatalf("output %q", out.String())
	}
}

func TestCLI_checkUpdate_json(t *testing.T) {
	t.Cleanup(resetCLIState)
	dir := t.TempDir()
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

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "find-for-updates") {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprintf(w, `{"version":"2.0.0","download_url":"http://%s/artifact"}`, r.Host)
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)

	out := new(strings.Builder)
	bootroot.RootCmd.SetOut(out)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"check-update", "--api-base-url", srv.URL, "--data-dir", dir, "--json"})
	if err := bootroot.Execute(); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	var result CheckUpdateResult
	if err := json.Unmarshal([]byte(out.String()), &result); err != nil {
		t.Fatalf("decode JSON: %v — output: %q", err, out.String())
	}
	if !result.UpdateAvailable || result.InstalledVersion != "1.0.0" || result.LatestVersion != "2.0.0" {
		t.Fatalf("unexpected result: %+v", result)
	}
}

func TestCLI_update_rollbackOnDownloadFailure(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("requires fake systemctl script")
	}
	t.Cleanup(resetCLIState)

	dir := t.TempDir()
	oldBin := install.BinaryPath(dir)
	if err := os.MkdirAll(filepath.Dir(oldBin), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(oldBin, []byte("old-binary"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := install.SaveState(install.StatePath(dir), &install.State{
		Version:    "1.0.0",
		BinaryPath: oldBin,
	}); err != nil {
		t.Fatal(err)
	}

	// Server returns update available but download endpoint fails.
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "find-for-updates") {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprintf(w, `{"version":"2.0.0","download_url":"http://%s/artifact"}`, r.Host)
			return
		}
		if r.URL.Path == "/artifact" {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)

	stubDir := t.TempDir()
	stub := filepath.Join(stubDir, "systemctl")
	if err := os.WriteFile(stub, []byte("#!/bin/sh\nexit 0\n"), 0o755); err != nil {
		t.Fatal(err)
	}
	oldPath := os.Getenv("PATH")
	t.Cleanup(func() { _ = os.Setenv("PATH", oldPath) })
	_ = os.Setenv("PATH", stubDir+string(os.PathListSeparator)+oldPath)

	bootroot.RootCmd.SetOut(io.Discard)
	bootroot.RootCmd.SetErr(io.Discard)
	t.Cleanup(func() {
		bootroot.RootCmd.SetOut(os.Stdout)
		bootroot.RootCmd.SetErr(os.Stderr)
	})

	bootroot.RootCmd.SetArgs([]string{"update", "--api-base-url", srv.URL, "--data-dir", dir})
	err := bootroot.Execute()
	if err == nil {
		t.Fatal("expected error from failed download")
	}

	// Old bundle must be restored.
	if _, statErr := os.Stat(oldBin); statErr != nil {
		t.Fatalf("old binary missing after rollback: %v", statErr)
	}
	// Backup dir must be cleaned up.
	if _, statErr := os.Stat(install.BundleBackupDir(dir)); !os.IsNotExist(statErr) {
		t.Fatal("expected backup dir removed after rollback")
	}
	// install.json must still reflect old version.
	st, loadErr := install.LoadState(install.StatePath(dir))
	if loadErr != nil || st == nil || st.Version != "1.0.0" {
		t.Fatalf("state after rollback: %+v err %v", st, loadErr)
	}
}
