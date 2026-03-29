package bootstrap

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// ComposeCmd executa `docker compose -f <compose> ...` com working directory na pasta do compose.
func ComposeCmd(ctx context.Context, composePath string, args ...string) *exec.Cmd {
	dir := filepath.Dir(composePath)
	full := append([]string{"compose", "-f", composePath}, args...)
	cmd := exec.CommandContext(ctx, "docker", full...)
	cmd.Dir = dir
	return cmd
}

// ComposeRun executa docker compose e devolve erro se o exit code for não zero.
func ComposeRun(ctx context.Context, composePath string, args ...string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Minute)
	defer cancel()
	cmd := ComposeCmd(ctx, composePath, args...)
	var buf bytes.Buffer
	cmd.Stdout = &buf
	cmd.Stderr = &buf
	err := cmd.Run()
	out := buf.Bytes()
	if err != nil {
		return out, fmt.Errorf("docker compose %s: %w\n%s", strings.Join(args, " "), err, strings.TrimSpace(string(out)))
	}
	return out, nil
}
