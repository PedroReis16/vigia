package main

import (
	"log"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
)

func newRouter() *gin.Engine {
	r := gin.Default()
	r.GET("/gerenciamento-dispositivos/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "Bem vindo ao Vigia! Sua plataforma para o cuidado de quem você mais ama",
		})
	})
	return r
}

func resolveAPIAddr() string {
	addr := strings.TrimSpace(os.Getenv("VIGIA_API_ADDR"))
	if addr == "" {
		return "127.0.0.1:8000"
	}
	return addr
}

func main() {
	r := newRouter()
	addr := resolveAPIAddr()
	if err := r.Run(addr); err != nil {
		log.Fatalf("gin: %v", err)
	}
}