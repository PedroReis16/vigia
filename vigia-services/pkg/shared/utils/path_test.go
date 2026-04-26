package utils

import (
	"path/filepath"
	"testing"
)

func TestGetCompletePath(t *testing.T) {
	t.Setenv("HOME", "/tmp/test-home")

	tests := []struct {
		name  string
		input string
		want  string
	}{
		{
			name:  "returns home for tilde only",
			input: "~",
			want:  "/tmp/test-home",
		},
		{
			name:  "expands path with tilde slash prefix",
			input: "~/configs/app.yaml",
			want:  filepath.Join("/tmp/test-home", "configs/app.yaml"),
		},
		{
			name:  "returns input when no tilde prefix",
			input: "/etc/app/config.yaml",
			want:  "/etc/app/config.yaml",
		},
		{
			name:  "keeps current behavior for tilde without slash",
			input: "~arquivo",
			want:  filepath.Join("/tmp/test-home", "~arquivo"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := GetCompletePath(tt.input)
			if got != tt.want {
				t.Fatalf("GetCompletePath(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}
