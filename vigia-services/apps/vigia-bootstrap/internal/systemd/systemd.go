package systemd

import (
	"context"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

const defaultTimeout = 2 * time.Minute

// Runner invokes systemctl for a unit name without requiring the ".service" suffix.
type Runner struct {
	Unit string
}

func (r *Runner) serviceName() string {
	u := strings.TrimSpace(r.Unit)
	u = strings.TrimSuffix(u, ".service")
	if u == "" {
		return ""
	}
	return u + ".service"
}

func (r *Runner) run(ctx context.Context, args ...string) error {
	name := r.serviceName()
	if name == "" {
		return fmt.Errorf("systemd unit name is empty")
	}
	if ctx == nil {
		ctx = context.Background()
	}
	ctx, cancel := context.WithTimeout(ctx, defaultTimeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, "systemctl", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("%w: %s", err, strings.TrimSpace(string(out)))
	}
	return nil
}

// Start runs systemctl start.
func (r *Runner) Start(ctx context.Context) error {
	return r.run(ctx, "start", r.serviceName())
}

// Stop runs systemctl stop.
func (r *Runner) Stop(ctx context.Context) error {
	return r.run(ctx, "stop", r.serviceName())
}

// Restart runs systemctl restart.
func (r *Runner) Restart(ctx context.Context) error {
	return r.run(ctx, "restart", r.serviceName())
}

// EnableNow runs systemctl enable --now.
func (r *Runner) EnableNow(ctx context.Context) error {
	return r.run(ctx, "enable", "--now", r.serviceName())
}
