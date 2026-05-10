package config

import (
	"context"

	"github.com/PedroReis16/vigia/vigia-services/pkg/shared/logger"
	"go.uber.org/fx"
	"go.uber.org/zap"
)

const logProjectName = "vigia-api"

// NewLogger cria o zap.Logger compartilhado e registra no Lifecycle o flush dos buffers ao encerrar a aplicação.
func NewLogger(lc fx.Lifecycle) *zap.Logger {
	log := logger.NewLogger(logProjectName).With(zap.String("service", logProjectName))

	lc.Append(fx.Hook{
		OnStop: func(ctx context.Context) error {
			// Sync pode falhar em stderr quando não há TTY; ignorar é comum no shutdown.
			_ = log.Sync()
			return nil
		},
	})

	return log
}
