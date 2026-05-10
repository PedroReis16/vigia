package handlers

import (
	"net/http"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/services"
	"github.com/gin-gonic/gin"
)

type DevicesHandler struct {
	service *services.DeviceService
}

func NewDevicesHandler(service *services.DeviceService) *DevicesHandler {
	return &DevicesHandler{service: service}
}

func (h *DevicesHandler) RegisterUserDevice(c *gin.Context) {
	// Vincula um dispositivo a um usuário

	c.JSON(http.StatusOK, gin.H{"message": "Hello, World!"})
}

func (h *DevicesHandler) GetDevices(c *gin.Context) {

	// Retorna os dispositivos cadastrados para o usuário

	c.JSON(http.StatusOK, gin.H{"message": "Hello, World!"})
}

func (h *DevicesHandler) DownloadVigiaVersion(c *gin.Context) {

	// Baixa a versão do Vigia para o dispositivo

	// Se for passado o parâmetro de uma versão específica, será retornado a versão, se não a última versão disponível

	c.JSON(http.StatusOK, gin.H{"message": "Hello, World!"})
}
