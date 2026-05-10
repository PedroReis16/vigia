package http

import (
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/gin-gonic/gin"
)

func SetRoutes(router *gin.Engine) {
	router.GET("/health", handlers.HealthCheckHandler)

	v1 := router.Group("/v1")
	{
		devices := v1.Group("/devices")
		{
			devices.GET("/", )
		}
	}
}