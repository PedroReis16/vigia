package logger

import (
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCreateFilePath(t *testing.T) {
	homeDir := t.TempDir()
	t.Setenv("HOME", homeDir)

	projectName := "unit-project"
	got := createFilePath(projectName)
	want := filepath.Join(homeDir, "vigia", "logs", projectName, projectName+".log")

	if got != want {
		t.Fatalf("createFilePath(%q) = %q, want %q", projectName, got, want)
	}

	info, err := os.Stat(got)
	if err != nil {
		t.Fatalf("expected path %q to exist: %v", got, err)
	}

	if !info.IsDir() {
		t.Fatalf("expected %q to be a directory based on current implementation", got)
	}
}

func TestNewLoggerWritesDebugToConsole(t *testing.T) {
	homeDir := t.TempDir()
	t.Setenv("HOME", homeDir)

	originalStdout := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("failed to create stdout pipe: %v", err)
	}
	defer r.Close()
	defer w.Close()

	os.Stdout = w
	t.Cleanup(func() {
		os.Stdout = originalStdout
	})

	logger := NewLogger("logger-console-test")
	if logger == nil {
		t.Fatal("NewLogger returned nil")
	}

	logger.Debug("debug-message-visible-on-console")
	_ = logger.Sync()

	if err := w.Close(); err != nil {
		t.Fatalf("failed to close write pipe: %v", err)
	}

	output, err := io.ReadAll(r)
	if err != nil {
		t.Fatalf("failed to read captured stdout: %v", err)
	}

	if !strings.Contains(string(output), "debug-message-visible-on-console") {
		t.Fatalf("expected debug message in console output, got %q", string(output))
	}
}
