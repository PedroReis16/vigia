package config

import (
	"context"
	"errors"
	"net"
	"net/http"
	"time"

	routes "github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/middleware"

	"github.com/gin-gonic/gin"
	"go.uber.org/fx"
	"go.uber.org/zap"
)

func Server(lc fx.Lifecycle, log *zap.Logger, handlers *handlers.Handlers) *gin.Engine {
	router := gin.New()
	router.Use(middleware.RequestContext(log))
	router.Use(middleware.ZapRecovery())

	routes.SetRoutes(router, handlers)
	srv := &http.Server{
		Addr:    ":8000",
		Handler: router,
		// G112 / Slowloris: tempo máximo para ler cabeçalhos antes do corpo (Go exige para mitigar).
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       60 * time.Second,
		WriteTimeout:      60 * time.Second,
		IdleTimeout:       120 * time.Second,
	}

	lc.Append(fx.Hook{
		OnStart: func(ctx context.Context) error {
			ln, err := net.Listen("tcp", srv.Addr)
			if err != nil {
				log.Error("failed to start HTTP server", zap.String("addr", srv.Addr), zap.Error(err))
				return err
			}
			go func() {
				if err := srv.Serve(ln); err != nil && !errors.Is(err, http.ErrServerClosed) {
					log.Error("HTTP server stopped unexpectedly", zap.Error(err))
				}
			}()
			log.Info("HTTP server listening", zap.String("addr", srv.Addr))
			return nil
		},
		OnStop: func(ctx context.Context) error {
			if err := srv.Shutdown(ctx); err != nil {
				log.Error("HTTP server shutdown", zap.Error(err))
				return err
			}
			log.Info("HTTP server stopped")
			return nil
		},
	})

	return router
}
