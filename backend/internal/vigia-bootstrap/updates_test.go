package bootstrap

import (
	"context"
	"os"
	"path/filepath"
	"testing"
)

func TestMergeImageRefs(t *testing.T) {
	got := mergeImageRefs(
		[]string{"a:1", " b:2 ", "a:1"},
		[]string{"c:3", "a:1"},
	)
	want := []string{"a:1", "b:2", "c:3"}
	if len(got) != len(want) {
		t.Fatalf("len %d want %d: %v", len(got), len(want), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("got[%d]=%q want %q", i, got[i], want[i])
		}
	}
}

func TestInitialStackUp_noImages(t *testing.T) {
	dir := t.TempDir()
	compose := filepath.Join(dir, "docker-compose.yaml")
	if err := os.WriteFile(compose, []byte("version: \"3.8\"\nservices: {}\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	cfg := Config{DataDir: dir}
	if err := InitialStackUp(context.Background(), cfg); err != nil {
		t.Fatal(err)
	}
}

func TestDigestContained(t *testing.T) {
	local := "nginx@sha256:deadbeefcafe"
	remote := "sha256:deadbeefcafe"
	if !digestContained(local, remote) {
		t.Fatal("expected match")
	}
	if digestContained(local, "sha256:other") {
		t.Fatal("expected no match")
	}
	if digestContained("", "sha256:x") {
		t.Fatal("empty local should not match")
	}
}
