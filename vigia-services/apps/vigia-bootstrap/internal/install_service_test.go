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

func TestExecStartLineQuotingCases(t *testing.T) {
	cases := []struct {
		name     string
		execPath string
		dataDir  string
		wantSub  []string // each must appear in line
	}{
		{
			name:     "plain_paths_unquoted",
			execPath: "/usr/bin/vigia-bootstrap",
			dataDir:  "/var/lib/vigia/bootstrap",
			wantSub:  []string{"/usr/bin/vigia-bootstrap --data-dir /var/lib/vigia/bootstrap"},
		},
		{
			name:     "spaces_in_datadir",
			execPath: "/bin/vigia-bootstrap",
			dataDir:  "/var/lib/my data",
			wantSub: []string{
				"/bin/vigia-bootstrap --data-dir ",
				strconv.Quote("/var/lib/my data"),
			},
		},
		{
			name:     "spaces_in_exec_path",
			execPath: "/opt/my apps/vigia-bootstrap",
			dataDir:  "/var/lib/v",
			wantSub: []string{
				strconv.Quote("/opt/my apps/vigia-bootstrap"),
				"--data-dir /var/lib/v",
			},
		},
		{
			name:     "tab_in_datadir_triggers_quote",
			execPath: "/bin/v",
			dataDir:  "/var/x\tz",
			wantSub: []string{
				strconv.Quote("/var/x\tz"),
			},
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			line := ExecStartLine(tc.execPath, tc.dataDir)
			for _, sub := range tc.wantSub {
				if !strings.Contains(line, sub) {
					t.Fatalf("line %q missing %q", line, sub)
				}
			}
		})
	}
}

func TestSystemdUnitContent_ExecStartQuotesPathsWithSpaces(t *testing.T) {
	s := SystemdUnitContent("/var/data", "/opt/my bin/vigia-bootstrap")
	if !strings.Contains(s, `ExecStart=`+strconv.Quote("/opt/my bin/vigia-bootstrap")) {
		t.Fatalf("ExecStart should quote spaced binary path: %s", s)
	}
	if !strings.Contains(s, `--data-dir /var/data`) {
		t.Fatalf("missing clean data-dir in ExecStart: %s", s)
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

func TestPrepareBootstrapDataDirsInvalid(t *testing.T) {
	// filepath.Clean maps "", ".", and "./." to "." which is rejected.
	for _, dir := range []string{"", ".", "./."} {
		if err := PrepareBootstrapDataDirs(dir); err == nil {
			t.Fatalf("PrepareBootstrapDataDirs(%q) want error", dir)
		} else if !strings.Contains(err.Error(), "invalid data directory") {
			t.Fatalf("unexpected error for %q: %v", dir, err)
		}
	}
}

func TestPrepareBootstrapDataDirsMkdirBlocked(t *testing.T) {
	base := t.TempDir()
	blockFile := filepath.Join(base, "block")
	if err := os.WriteFile(blockFile, []byte("x"), 0644); err != nil {
		t.Fatal(err)
	}
	badData := filepath.Join(blockFile, "nested")
	err := PrepareBootstrapDataDirs(badData)
	if err == nil {
		t.Fatal("expected error when parent path is a file")
	}
}

func TestResolveExecutablePath(t *testing.T) {
	p, err := resolveExecutablePath()
	if err != nil {
		t.Fatal(err)
	}
	if p == "" {
		t.Fatal("empty executable path")
	}
	if st, err := os.Stat(p); err != nil {
		t.Fatalf("stat resolved path: %v", err)
	} else if st.IsDir() {
		t.Fatal("executable path is a directory")
	}
}

func TestInstallSystemdUnitUnsupportedOS(t *testing.T) {
	if runtime.GOOS == "linux" {
		t.Skip("covered by Linux-specific tests")
	}
	err := InstallSystemdUnit("/tmp/x", false)
	if err == nil {
		t.Fatal("expected error outside Linux")
	}
	if !strings.Contains(err.Error(), "Linux") {
		t.Fatalf("got %v", err)
	}
}

func TestInstallSystemdUnitInvalidDataDir(t *testing.T) {
	if runtime.GOOS != "linux" {
		t.Skip("invalid data-dir branch runs after Linux check")
	}
	for _, dir := range []string{".", "", "./."} {
		err := InstallSystemdUnit(dir, false)
		if err == nil || !strings.Contains(err.Error(), "invalid data-dir") {
			t.Fatalf("InstallSystemdUnit(%q) = %v, want invalid data-dir", dir, err)
		}
	}
}

func TestInstallSystemdUnitPrepareDataDirFails(t *testing.T) {
	if runtime.GOOS != "linux" {
		t.Skip("InstallSystemdUnit full path only on Linux")
	}
	base := t.TempDir()
	blockFile := filepath.Join(base, "not-a-dir")
	if err := os.WriteFile(blockFile, []byte("x"), 0644); err != nil {
		t.Fatal(err)
	}
	bad := filepath.Join(blockFile, "data")
	err := InstallSystemdUnit(bad, false)
	if err == nil {
		t.Fatal("expected prepare data-dir error")
	}
	if !strings.Contains(err.Error(), "prepare data-dir") {
		t.Fatalf("got %v", err)
	}
}

func TestUninstallSystemdUnitUnsupportedOS(t *testing.T) {
	if runtime.GOOS == "linux" {
		t.Skip("linux would run real systemctl")
	}
	if err := UninstallSystemdUnit(false); err == nil {
		t.Fatal("expected error outside Linux")
	}
}
