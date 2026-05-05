package main

import (
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/config"
	"github.com/gin-gonic/gin"
	"go.uber.org/fx"
)

func main() {
	app := fx.New(
		fx.Provide(
			config.Server,
		),
		fx.Invoke(func(*gin.Engine) {}),
	)
	app.Run()
}
