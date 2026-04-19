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
