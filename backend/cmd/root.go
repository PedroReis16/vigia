package cmd

import (
	"github.com/gin-gonic/gin"
)

func Execute() error {
	r := gin.Default()
	r.GET("/gerenciamento-dispositivos/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "Bem vindo ao Vigia! Sua plataforma para o cuidado de quem você mais ama",
		})
	})
	return r.Run(":8000")
}
