package http

import (
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

func SetRoutes(router *gin.Engine) {
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	router.GET("/health", handlers.HealthCheckHandler)

	v1 := router.Group("/v1")
	{
		devices := v1.Group("/devices")
		{
			devices.POST("/register", handlers.NewDevicesHandler().RegisterUserDevice)
			devices.GET("/", handlers.NewDevicesHandler().GetDevices)
			devices.GET("/download", handlers.NewDevicesHandler().DownloadVigiaVersion)
		}
	}
}