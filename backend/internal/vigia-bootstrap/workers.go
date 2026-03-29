package bootstrap

import (
	"context"
	"fmt"
	"log"
	"time"

	"golang.org/x/sync/errgroup"
)

// Job descreve uma rotina periódica.
type Job struct {
	Name     string
	Interval time.Duration
	// IntervalFn, se não nil, substitui Interval no início de cada ciclo (após cada execução).
	IntervalFn func() time.Duration
	// RunImmediately executa Fn uma vez antes do primeiro intervalo.
	RunImmediately bool
	Fn             func(context.Context) error
}

// RunJobs inicia cada job em goroutine; o primeiro erro não-nil cancela o contexto do grupo.
func RunJobs(ctx context.Context, jobs []Job) error {
	g, ctx := errgroup.WithContext(ctx)

	for _, j := range jobs {
		job := j
		if job.Interval <= 0 && job.IntervalFn == nil {
			return fmt.Errorf("job %q: intervalo inválido", job.Name)
		}
		if job.Fn == nil {
			return fmt.Errorf("job %q: Fn é obrigatório", job.Name)
		}

		g.Go(func() error {
			return runPeriodic(ctx, job)
		})
	}

	return g.Wait()
}

func effectiveInterval(job Job) time.Duration {
	if job.IntervalFn != nil {
		if d := job.IntervalFn(); d > 0 {
			return d
		}
	}
	if job.Interval > 0 {
		return job.Interval
	}
	return 5 * time.Minute
}

func runPeriodic(ctx context.Context, job Job) error {
	run := func() error {
		if err := job.Fn(ctx); err != nil {
			return fmt.Errorf("[%s] %w", job.Name, err)
		}
		return nil
	}

	if job.RunImmediately {
		if err := run(); err != nil {
			return err
		}
	}

	for {
		select {
		case <-ctx.Done():
			log.Printf("[%s] encerrando: %v", job.Name, ctx.Err())
			return nil
		case <-time.After(effectiveInterval(job)):
			if err := run(); err != nil {
				return err
			}
		}
	}
}
