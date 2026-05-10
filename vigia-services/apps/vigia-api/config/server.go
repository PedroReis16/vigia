package config

import (
	"context"
	"net"
	"net/http"

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
	}

	lc.Append(fx.Hook{
		OnStart: func(ctx context.Context) error {
			ln, err := net.Listen("tcp", srv.Addr)
			if err != nil {
				log.Error("failed to start HTTP server", zap.String("addr", srv.Addr), zap.Error(err))
				return err
			}
			go srv.Serve(ln)
			log.Info("HTTP server listening", zap.String("addr", srv.Addr))
			return nil
		},
		OnStop: func(ctx context.Context) error {
			srv.Shutdown(ctx)
			log.Info("HTTP server stopped")
			return nil
		},
	})

	return router
}
