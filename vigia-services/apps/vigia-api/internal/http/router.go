package http

import (
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

func SetRoutes(router *gin.Engine, handlers *handlers.Handlers) {
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	router.GET("/health", handlers.HealthCheckHandler.Handle)

	v1 := router.Group("/v1")
	{
		group := v1.Group("/devices")
		{
			group.POST("/register", handlers.DevicesHandler.RegisterUserDevice)
			group.GET("/", handlers.DevicesHandler.GetDevices)
			group.GET("/download", handlers.DevicesHandler.DownloadVigiaVersion)
		}
	}
}