package config

import (
	"context"
	"fmt"
	"net"
	"net/http"
	
	routes "github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http"

	"github.com/gin-gonic/gin"
	"go.uber.org/fx"
)

func Server(lc fx.Lifecycle) *gin.Engine {
	router := gin.Default()


	routes.SetRoutes(router)
	srv := &http.Server{
		Addr:    ":8000",
		Handler: router,
	}

	lc.Append(fx.Hook{
		OnStart: func(ctx context.Context) error {
			ln, err := net.Listen("tcp", srv.Addr) // the web server starts listening on 8080
			if err != nil {
				fmt.Println("[Vigia API] Failed to start HTTP Server at", srv.Addr)
				return err
			}
			go srv.Serve(ln) // process an incoming request in a go routine
			fmt.Println("[Vigia API]Succeeded to start HTTP Server at", srv.Addr)
			return nil
		},
		OnStop: func(ctx context.Context) error {
			srv.Shutdown(ctx) // stop the web server
			fmt.Println("[Vigia API] HTTP Server is stopped")
			return nil
		},
	})

	return router
}
