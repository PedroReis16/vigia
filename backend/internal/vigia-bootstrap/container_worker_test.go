package vigiabootstrap

import "testing"

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

func TestSplitRepositoryAndTagHubImageWithTag(t *testing.T) {
	repo, tag, err := splitRepositoryAndTag("pedroreis16/fall-detection:latest")
	if err != nil {
		t.Fatal(err)
	}
	if want := "pedroreis16/fall-detection"; repo != want {
		t.Errorf("repo = %q, want %q", repo, want)
	}
	if want := "latest"; tag != want {
		t.Errorf("tag = %q, want %q", tag, want)
	}
}
