package vigiabootstrap

import (
	"os"
	"path/filepath"
	"testing"
)

func restoreBootstrapEnv(t *testing.T, old string, had bool) {
	t.Helper()
	t.Cleanup(func() {
		if had {
			_ = os.Setenv("VIGIA_BOOTSTRAP_DATA_DIR", old)
		} else {
			_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")
		}
	})
}

func TestApplyBootstrapDataDirFromArgsDoubleDash(t *testing.T) {
	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)
	_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")

	ApplyBootstrapDataDirFromArgs([]string{"vigia-bootstrap", "--data-dir", "/tmp/z"})
	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != filepath.Clean("/tmp/z") {
		t.Fatalf("got %q", got)
	}
}

func TestApplyBootstrapDataDirFromArgsEqualsForm(t *testing.T) {
	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)
	_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")

	ApplyBootstrapDataDirFromArgs([]string{"vigia-bootstrap", "-data-dir=/tmp/a"})
	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != filepath.Clean("/tmp/a") {
		t.Fatalf("got %q", got)
	}
}

func TestApplyBootstrapDataDirFromArgsVariants(t *testing.T) {
	cases := []struct {
		name string
		argv []string
		want string
	}{
		{
			name: "single-dash space",
			argv: []string{"vigia-bootstrap", "-data-dir", "/tmp/dd-space"},
			want: filepath.Clean("/tmp/dd-space"),
		},
		{
			name: "double-dash equals",
			argv: []string{"bin", "--data-dir=/tmp/dd-eq"},
			want: filepath.Clean("/tmp/dd-eq"),
		},
		{
			name: "single-dash equals",
			argv: []string{"bin", "-data-dir=/tmp/dd-seq"},
			want: filepath.Clean("/tmp/dd-seq"),
		},
		{
			name: "trim value",
			argv: []string{"bin", "--data-dir", "  /tmp/spaced  "},
			want: filepath.Clean("/tmp/spaced"),
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
			restoreBootstrapEnv(t, old, had)
			_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")

			ApplyBootstrapDataDirFromArgs(tc.argv)
			if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != tc.want {
				t.Fatalf("got %q, want %q", got, tc.want)
			}
		})
	}
}

func TestApplyBootstrapDataDirFromArgsFirstMatchWins(t *testing.T) {
	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)
	_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")

	ApplyBootstrapDataDirFromArgs([]string{"vigia-bootstrap", "--data-dir", "/tmp/one", "--data-dir", "/tmp/two"})
	want := filepath.Clean("/tmp/one")
	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != want {
		t.Fatalf("got %q, want %q", got, want)
	}
}

func TestApplyBootstrapDataDirFromArgsNoValue(t *testing.T) {
	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)
	_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")

	// Trailing flag with no argv[i+1] — must not Setenv.
	ApplyBootstrapDataDirFromArgs([]string{"vigia-bootstrap", "--data-dir"})
	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != "" {
		t.Fatalf("expected empty env, got %q", got)
	}

	_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")
	ApplyBootstrapDataDirFromArgs([]string{"vigia-bootstrap", "--data-dir="})
	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != "" {
		t.Fatalf("empty equals form: expected empty env, got %q", got)
	}
}

func TestApplyBootstrapDataDirFromArgsSingleProgramName(t *testing.T) {
	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)
	_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")

	ApplyBootstrapDataDirFromArgs([]string{"vigia-bootstrap"})
	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != "" {
		t.Fatalf("expected empty env, got %q", got)
	}
}

func TestApplyBootstrapDataDirFromEtcFilePreservesEnvWhenSet(t *testing.T) {
	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)

	const sentinel = "/tmp/vigia-bootstrap-etc-test-sentinel"
	_ = os.Setenv("VIGIA_BOOTSTRAP_DATA_DIR", sentinel)

	ApplyBootstrapDataDirFromEtcFile()

	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != sentinel {
		t.Fatalf("env changed to %q; expected %q", got, sentinel)
	}
}

func TestApplyBootstrapDataDirFromEtcFileMissingFile(t *testing.T) {
	if _, err := os.Stat(EtcBootstrapDataDirPath); err == nil {
		t.Skipf("%s exists; skipping (would depend on file contents)", EtcBootstrapDataDirPath)
	}

	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)
	_ = os.Unsetenv("VIGIA_BOOTSTRAP_DATA_DIR")

	ApplyBootstrapDataDirFromEtcFile()

	if got := os.Getenv("VIGIA_BOOTSTRAP_DATA_DIR"); got != "" {
		t.Fatalf("expected empty env when etc file missing, got %q", got)
	}
}

func TestWriteEtcBootstrapDataDirEmptyAndDotNoOp(t *testing.T) {
	cases := []struct {
		name string
		dir  string
	}{
		{"empty", ""},
		{"whitespace_only", " "},
		{"dot", "."},
		{"dot_trimmed", " . "},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if err := WriteEtcBootstrapDataDir(tc.dir); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestRemoveEtcBootstrapDataDirNoPanic(t *testing.T) {
	RemoveEtcBootstrapDataDir()
}
