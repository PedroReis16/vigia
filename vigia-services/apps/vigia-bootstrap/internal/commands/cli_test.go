package commands

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

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

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		base := "http://" + r.Host
		if strings.Contains(r.URL.Path, "find-for-updates") {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprintf(w, `{"version":"2.0.0","download_url":"%s/artifact"}`, base)
			return
		}
		if r.URL.Path == "/artifact" {
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("#!/bin/sh\ntrue\n"))
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
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		base := "http://" + r.Host
		if strings.Contains(r.URL.Path, "/v1/devices/version/find-for-updates") {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprintf(w, `{"version":"1.0.0","download_url":"%s/artifact"}`, base)
			return
		}
		if r.URL.Path == "/artifact" {
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("#!/bin/sh\ntrue\n"))
			return
		}
		http.NotFound(w, r)
	}))
	t.Cleanup(srv.Close)
	return srv
}

func resetCLIState() {
	config.APIBaseURL = ""
	config.DataDir = ""
	config.SystemdUnit = ""
	startAfterInstall = false
	bootroot.RootCmd.SetArgs(nil)
}
