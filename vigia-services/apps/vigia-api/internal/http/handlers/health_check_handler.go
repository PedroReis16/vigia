package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func HealthCheckHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "Bem vindo ao Vigia! Sua plataforma para o cuidado de quem você mais ama"})
}