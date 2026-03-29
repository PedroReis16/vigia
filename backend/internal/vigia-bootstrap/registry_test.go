package bootstrap

import "testing"

func TestParseRepoTag(t *testing.T) {
	tests := []struct {
		ref              string
		wantRepo         string
		wantTag          string
		wantPinnedDigest bool
	}{
		{"nginx:latest", "library/nginx", "latest", false},
		{"nginx", "library/nginx", "latest", false},
		{"bitnami/nginx:1.2.3", "bitnami/nginx", "1.2.3", false},
		{"docker.io/library/alpine:3", "docker.io/library/alpine", "3", false},
		{"my/alpine@sha256:abc", "my/alpine", "", true},
	}
	for _, tt := range tests {
		t.Run(tt.ref, func(t *testing.T) {
			repo, tag, pinned := parseRepoTag(tt.ref)
			if pinned != tt.wantPinnedDigest {
				t.Fatalf("pinned: got %v want %v", pinned, tt.wantPinnedDigest)
			}
			if repo != tt.wantRepo {
				t.Fatalf("repo: got %q want %q", repo, tt.wantRepo)
			}
			if !pinned && tag != tt.wantTag {
				t.Fatalf("tag: got %q want %q", tag, tt.wantTag)
			}
		})
	}
}
