package systemd

import (
	"context"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestRunner_serviceName(t *testing.T) {
	tests := []struct {
		unit string
		want string
	}{
		{"fall-detection", "fall-detection.service"},
		{"  fd  ", "fd.service"},
		{"foo.service", "foo.service"},
		{"", ""},
	}
	for _, tc := range tests {
		r := &Runner{Unit: tc.unit}
		if got := r.serviceName(); got != tc.want {
			t.Fatalf("Unit %q: got %q want %q", tc.unit, got, tc.want)
		}
	}
}

func TestRunner_Start_emptyUnit(t *testing.T) {
	r := &Runner{Unit: "   "}
	err := r.Start(context.Background())
	if err == nil || !strings.Contains(err.Error(), "empty") {
		t.Fatalf("got err=%v", err)
	}
}

func TestRunner_Start_fakeSystemctl(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("requires executable shell script as systemctl stub")
	}
	dir := t.TempDir()
	stub := filepath.Join(dir, "systemctl")
	script := "#!/bin/sh\nexit 0\n"
	if err := os.WriteFile(stub, []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	oldPath := os.Getenv("PATH")
	t.Cleanup(func() { _ = os.Setenv("PATH", oldPath) })
	_ = os.Setenv("PATH", dir+string(os.PathListSeparator)+oldPath)

	r := &Runner{Unit: "fall-detection"}
	if err := r.Start(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := r.Stop(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := r.Restart(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := r.EnableNow(context.Background()); err != nil {
		t.Fatal(err)
	}
}
