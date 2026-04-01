package main

import (
	"log"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()
	r.GET("/gerenciamento-dispositivos/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "Bem vindo ao Vigia! Sua plataforma para o cuidado de quem você mais ama",
		})
	})
	addr := strings.TrimSpace(os.Getenv("VIGIA_API_ADDR"))
	if addr == "" {
		addr = "127.0.0.1:8000"
	}
	if err := r.Run(addr); err != nil {
		log.Fatalf("gin: %v", err)
	}
}