package bootstrap

import (
	"strings"
	"testing"
)

func TestQuoteSystemdWord(t *testing.T) {
	if quoteSystemdWord("/a/b") != "/a/b" {
		t.Fatal("plain path")
	}
	if quoteSystemdWord("/a b/c") != `"/a b/c"` {
		t.Fatal("path with space", quoteSystemdWord("/a b/c"))
	}
}

func TestRenderSystemdUnit(t *testing.T) {
	out := renderSystemdUnit("/usr/local/bin/vigia-bootstrap", "/var/lib/vigia/bootstrap")
	if !strings.Contains(out, "ExecStart=/usr/local/bin/vigia-bootstrap -data-dir /var/lib/vigia/bootstrap") {
		t.Fatalf("missing ExecStart: %s", out)
	}
	if !strings.Contains(out, "ExecStartPre=/bin/mkdir -p /var/lib/vigia/bootstrap") {
		t.Fatalf("missing ExecStartPre: %s", out)
	}
}

func TestRenderSystemdUnit_spaces(t *testing.T) {
	out := renderSystemdUnit("/opt/vigia with space/bin", "/var/lib/vigia/data dir")
	if !strings.Contains(out, `ExecStart="/opt/vigia with space/bin" -data-dir "/var/lib/vigia/data dir"`) {
		t.Fatalf("expected quoted paths: %s", out)
	}
}
