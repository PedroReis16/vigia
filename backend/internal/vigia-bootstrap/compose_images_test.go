package bootstrap

import (
	"os"
	"path/filepath"
	"testing"
)

func TestImagesFromCompose(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "docker-compose.yaml")
	yaml := `version: "3.8"
services:
  a:
    image: nginx:1
  b:
    build: .
  c:
    image: alpine:latest
`
	if err := os.WriteFile(path, []byte(yaml), 0o644); err != nil {
		t.Fatal(err)
	}
	imgs, err := ImagesFromCompose(path)
	if err != nil {
		t.Fatal(err)
	}
	if len(imgs) != 2 {
		t.Fatalf("want 2 images, got %v", imgs)
	}
}
