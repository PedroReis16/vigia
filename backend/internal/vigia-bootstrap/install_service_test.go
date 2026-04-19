package vigiabootstrap

import (
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"testing"
)

func TestSystemdUnitContent(t *testing.T) {
	s := SystemdUnitContent("/var/lib/vigia/bootstrap", "/usr/local/bin/vigia-bootstrap")
	if !strings.Contains(s, "Environment=VIGIA_BOOTSTRAP_DATA_DIR=/var/lib/vigia/bootstrap") {
		t.Fatalf("missing env: %s", s)
	}
	if !strings.Contains(s, "Environment=VIGIA_LOG_DIR=/var/lib/vigia/bootstrap/logs") {
		t.Fatalf("missing VIGIA_LOG_DIR: %s", s)
	}
	if strings.Contains(s, "WorkingDirectory=") {
		t.Fatalf("WorkingDirectory must not be set (systemd fails if dir missing before first run): %s", s)
	}
	if !strings.Contains(s, "SyslogIdentifier=vigia-bootstrap") {
		t.Fatalf("missing SyslogIdentifier: %s", s)
	}
	if !strings.Contains(s, "ExecStart=/usr/local/bin/vigia-bootstrap --data-dir /var/lib/vigia/bootstrap") {
		t.Fatalf("missing ExecStart with --data-dir: %s", s)
	}
}

func TestExecStartLineQuotesSpaces(t *testing.T) {
	line := ExecStartLine("/usr/local/bin/vigia-bootstrap", "/var/lib/weird dir/bootstrap")
	want := strconv.Quote("/var/lib/weird dir/bootstrap")
	if !strings.Contains(line, want) {
		t.Fatalf("expected %s in %s", want, line)
	}
}

func TestDropInResetWorkingDirectoryContainsWorkdirRoot(t *testing.T) {
	s := DropInResetWorkingDirectory()
	if !strings.Contains(s, "WorkingDirectory=/") {
		t.Fatalf("expected WorkingDirectory=/: %q", s)
	}
}

func TestPrepareBootstrapDataDirs(t *testing.T) {
	base := t.TempDir()
	data := filepath.Join(base, "data", "vigia")
	if err := PrepareBootstrapDataDirs(data); err != nil {
		t.Fatal(err)
	}
	if st, err := os.Stat(data); err != nil || !st.IsDir() {
		t.Fatalf("data dir: %v", err)
	}
	if st, err := os.Stat(filepath.Join(data, "logs")); err != nil || !st.IsDir() {
		t.Fatalf("logs dir: %v", err)
	}
}

func TestUninstallSystemdUnitUnsupportedOS(t *testing.T) {
	if runtime.GOOS == "linux" {
		t.Skip("linux would run real systemctl")
	}
	if err := UninstallSystemdUnit(); err == nil {
		t.Fatal("expected error outside Linux")
	}
}
