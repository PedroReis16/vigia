package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// HealthCheckResponse é o corpo JSON do health check.
type HealthCheckResponse struct {
	Message string `json:"message"`
}

// HealthCheckHandler godoc
// @Summary      Health check
// @Description  Verifica se a API está em execução.
// @Tags         health
// @Produce      json
// @Success      200  {object}  HealthCheckResponse
// @Router       /health [get]
func HealthCheckHandler(c *gin.Context) {
	c.JSON(http.StatusOK, HealthCheckResponse{Message: "Bem vindo ao Vigia! Sua plataforma para o cuidado de quem você mais ama"})
}