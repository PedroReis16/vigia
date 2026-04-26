package main

import (
	"os"
	"runtime"
	"slices"
	"sort"
	"strings"
	"syscall"
	"testing"
	"time"
)

func restoreBootstrapRuntimeEnv(t *testing.T) {
	t.Helper()
	oldDD, hadDD := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	oldLD, hadLD := os.LookupEnv("VIGIA_LOG_DIR")
	t.Cleanup(func() {
		if hadDD {
			_ = os.Setenv("VIGIA_BOOTSTRAP_DATA_DIR", oldDD)
		} else {
			_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")
		}
		if hadLD {
			_ = os.Setenv("VIGIA_LOG_DIR", oldLD)
		} else {
			_ = os.Unsetenv("VIGIA_LOG_DIR")
		}
	})
}

func TestExecute_SubcommandsRegistered(t *testing.T) {
	var names []string
	for _, c := range rootCmd.Commands() {
		names = append(names, c.Name())
	}
	sort.Strings(names)
	want := []string{"install-service", "uninstall-service"}
	if !slices.Equal(names, want) {
		t.Fatalf("commands = %v, want %v", names, want)
	}
}

func TestExecute_RootHasRunE(t *testing.T) {
	if rootCmd.RunE == nil {
		t.Fatal("root RunE is nil")
	}
}

func TestExecute_InvalidDataDir(t *testing.T) {
	restoreBootstrapRuntimeEnv(t)

	rootCmd.SetArgs([]string{"--data-dir", "."})
	defer rootCmd.SetArgs(nil)

	err := Execute()
	if err == nil {
		t.Fatal("expected error for invalid data directory")
	}
	if !strings.Contains(err.Error(), "invalid data directory") {
		t.Fatalf("error = %v, want substring invalid data directory", err)
	}
}

func TestExecute_RunDaemonExitsOnSIGTERM(t *testing.T) {
	restoreBootstrapRuntimeEnv(t)

	dir := t.TempDir()
	rootCmd.SetArgs([]string{"--data-dir", dir})
	defer rootCmd.SetArgs(nil)

	errCh := make(chan error, 1)
	go func() {
		errCh <- Execute()
	}()

	// Allow runDaemon to pass PrepareBootstrapDataDirs, worker.Start, and block on signals.
	time.Sleep(400 * time.Millisecond)
	if err := syscall.Kill(os.Getpid(), syscall.SIGTERM); err != nil {
		t.Fatal(err)
	}

	select {
	case err := <-errCh:
		if err != nil {
			t.Fatalf("Execute: %v", err)
		}
	case <-time.After(10 * time.Second):
		t.Fatal("timeout waiting for SIGTERM shutdown")
	}
}

func TestExecute_InstallServiceUnsupportedOS(t *testing.T) {
	if runtime.GOOS == "linux" {
		t.Skip("on Linux this hits systemd/install paths; run integration tests separately")
	}

	rootCmd.SetArgs([]string{"install-service", "--data-dir", t.TempDir()})
	defer rootCmd.SetArgs(nil)

	err := Execute()
	if err == nil {
		t.Fatal("expected error on non-Linux")
	}
	if !strings.Contains(err.Error(), "Linux") {
		t.Fatalf("error = %v, want substring Linux", err)
	}
}

func TestExecute_UninstallServiceUnsupportedOS(t *testing.T) {
	if runtime.GOOS == "linux" {
		t.Skip("on Linux this hits systemd; run integration tests separately")
	}

	rootCmd.SetArgs([]string{"uninstall-service"})
	defer rootCmd.SetArgs(nil)

	err := Execute()
	if err == nil {
		t.Fatal("expected error on non-Linux")
	}
	if !strings.Contains(err.Error(), "Linux") {
		t.Fatalf("error = %v, want substring Linux", err)
	}
}
