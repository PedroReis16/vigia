package main

import (
	_ "github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/docs"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/services"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/config"
	"github.com/gin-gonic/gin"
	"go.uber.org/fx"
)

// @title           Vigia API
// @version         1.0
// @description     API do Vigia Services.
// @host            localhost:8000
// @BasePath        /
func main() {

	// Inicializa o FX
	// A ordem dos provides é importante, pois o FX vai injetar as dependências na ordem em que foram declaradas
	// Primeiro o DeviceService, depois os Handlers, depois o Server
	// O Invoke é o último a ser executado, pois é o ponto de entrada da aplicação
	app := fx.New(
		fx.Provide(
			// Services 
			services.NewDeviceService,
		),
		fx.Provide(
			// Handlers
			handlers.NewDevicesHandler,
			handlers.NewHealthCheckHandler,
			handlers.NewFiwareHandler,
			handlers.NewHandlers),
		fx.Provide(
			// Server
			config.Server,
		),
		// Invoke é o último a ser executado, pois é o ponto de entrada da aplicação
		fx.Invoke(func(*gin.Engine) {}),
	)

	// Executa a aplicação
	app.Run()
}
