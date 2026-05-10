package main

import (
	_ "github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/docs"

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
	app := fx.New(
		fx.Provide(
			config.Server,
		),
		fx.Invoke(func(*gin.Engine) {}),
	)
	app.Run()
}
