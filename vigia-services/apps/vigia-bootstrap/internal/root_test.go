package internal

import (
	"bytes"
	"strings"
	"testing"
)

func TestExecute_versionSubcommand(t *testing.T) {
	buf := new(bytes.Buffer)
	RootCmd.SetOut(buf)
	RootCmd.SetErr(buf)
	RootCmd.SetArgs([]string{"version"})
	t.Cleanup(func() {
		RootCmd.SetArgs(nil)
	})

	if err := Execute(); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(buf.String(), "vigia-bootstrap") {
		t.Fatalf("output: %q", buf.String())
	}
}
