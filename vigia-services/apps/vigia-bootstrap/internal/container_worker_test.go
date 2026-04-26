package vigiabootstrap

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"go.uber.org/zap"
)

func TestDockerInspectOutputMeansNoLocalImage(t *testing.T) {
	tests := []struct {
		out  string
		want bool
	}{
		{"Error response from daemon: No such image: pedroreis16/foo:latest\n", true},
		{"Error response from daemon: No such object: xxx", true},
		{"could not find the image: nginx:missing", true},
		{"Cannot connect to the Docker daemon", false},
		{"", false},
	}
	for _, tt := range tests {
		if got := dockerInspectOutputMeansNoLocalImage(tt.out); got != tt.want {
			t.Errorf("%q: got %v want %v", tt.out, got, tt.want)
		}
	}
}

func TestSplitRepositoryAndTag(t *testing.T) {
	tests := []struct {
		ref      string
		wantRepo string
		wantTag  string
		wantErr  string
	}{
		{
			ref:      "pedroreis16/fall-detection:latest",
			wantRepo: "pedroreis16/fall-detection",
			wantTag:  "latest",
		},
		{
			ref:      "nginx",
			wantRepo: "library/nginx",
			wantTag:  "latest",
		},
		{
			ref:      "nginx:1.21",
			wantRepo: "library/nginx",
			wantTag:  "1.21",
		},
		{
			ref:      "docker.io/nginx:alpine",
			wantRepo: "library/nginx",
			wantTag:  "alpine",
		},
		{
			ref:      "docker.io/myorg/myimage:v2",
			wantRepo: "myorg/myimage",
			wantTag:  "v2",
		},
		{
			ref:      "  myorg/app:prod  ",
			wantRepo: "myorg/app",
			wantTag:  "prod",
		},
		{
			ref:     "nginx@sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
			wantErr: "Fixed image digest not supported",
		},
		{
			ref:     "repo/name:with/slash",
			wantErr: "Ambiguous image tag",
		},
	}
	for _, tt := range tests {
		t.Run(tt.ref, func(t *testing.T) {
			repo, tag, err := splitRepositoryAndTag(tt.ref)
			if tt.wantErr != "" {
				if err == nil || !strings.Contains(err.Error(), tt.wantErr) {
					t.Fatalf("splitRepositoryAndTag(%q) err = %v, want substring %q", tt.ref, err, tt.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatalf("splitRepositoryAndTag(%q): %v", tt.ref, err)
			}
			if repo != tt.wantRepo {
				t.Errorf("repo = %q, want %q", repo, tt.wantRepo)
			}
			if tag != tt.wantTag {
				t.Errorf("tag = %q, want %q", tag, tt.wantTag)
			}
		})
	}
}

func TestEqualDigests(t *testing.T) {
	tests := []struct {
		a, b string
		want bool
	}{
		{"sha256:abc", "sha256:abc", true},
		{"sha256:AbC", "sha256:aBc", true},
		{"abc", "sha256:abc", true},
		{"sha256:aaa", "sha256:bbb", false},
		{"  sha256:x  ", "sha256:X", true},
	}
	for _, tt := range tests {
		if got := equalDigests(tt.a, tt.b); got != tt.want {
			t.Errorf("equalDigests(%q, %q) = %v, want %v", tt.a, tt.b, got, tt.want)
		}
	}
}

func TestTrimSHA(t *testing.T) {
	if got := trimSHA("  sha256:deadbeef  "); got != "deadbeef" {
		t.Errorf("trimSHA = %q, want deadbeef", got)
	}
	if got := trimSHA("cafe"); got != "cafe" {
		t.Errorf("trimSHA = %q, want cafe", got)
	}
}

func TestEnsureFileExists_CreateAndRefresh(t *testing.T) {
	logger := zap.NewNop()
	dir := t.TempDir()
	p := filepath.Join(dir, "nested", "target.txt")

	if err := ensureFileExists(logger, p, []byte("v1")); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(p)
	if err != nil {
		t.Fatal(err)
	}
	if string(b) != "v1" {
		t.Fatalf("content = %q, want v1", b)
	}

	if err := ensureFileExists(logger, p, []byte("v1")); err != nil {
		t.Fatal(err)
	}
	b, _ = os.ReadFile(p)
	if string(b) != "v1" {
		t.Fatalf("unchanged content = %q", b)
	}

	if err := ensureFileExists(logger, p, []byte("v2")); err != nil {
		t.Fatal(err)
	}
	b, _ = os.ReadFile(p)
	if string(b) != "v2" {
		t.Fatalf("after update content = %q, want v2", b)
	}
}

func TestLoadComposeContainers_WithDataDir(t *testing.T) {
	old, had := os.LookupEnv("VIGIA_BOOTSTRAP_DATA_DIR")
	restoreBootstrapEnv(t, old, had)

	dir := t.TempDir()
	t.Setenv("VIGIA_BOOTSTRAP_DATA_DIR", dir)

	composePath, err := loadComposeContainers(zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	wantCompose := filepath.Join(dir, "docker-compose.yaml")
	if *composePath != wantCompose {
		t.Fatalf("compose path = %q, want %q", *composePath, wantCompose)
	}

	composeBytes, err := os.ReadFile(wantCompose)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(composeBytes, embeddedComposeFile) {
		t.Fatal("docker-compose.yaml does not match embedded content")
	}

	envPath := filepath.Join(dir, "default.env")
	envBytes, err := os.ReadFile(envPath)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(envBytes, embeddedBaseEnv) {
		t.Fatal("default.env does not match embedded content")
	}

	// Second call: files already match embedded bytes; should stay consistent.
	composePath2, err := loadComposeContainers(zap.NewNop())
	if err != nil {
		t.Fatal(err)
	}
	if *composePath2 != wantCompose {
		t.Fatalf("second call compose path = %q", *composePath2)
	}
}
