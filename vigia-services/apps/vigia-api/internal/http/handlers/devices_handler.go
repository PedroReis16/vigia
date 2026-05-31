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

// RegisterUserDevice godoc
// @Summary      Registrar dispositivo do usuário
// @Description  Vincula um dispositivo a um usuário autenticado.
// @Tags         devices
// @Accept       json
// @Produce      json
// @Success      200  {object}  MessageResponse
// @Failure      500  {object}  ErrorResponse
// @Router       /v1/devices/register [post]
func (h *DevicesHandler) RegisterUserDevice(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "Hello, World!"})
}

// GetDevices godoc
// @Summary      Listar dispositivos do usuário
// @Description  Retorna a lista de dispositivos cadastrados para o usuário autenticado.
// @Tags         devices
// @Produce      json
// @Success      200  {object}  MessageResponse
// @Failure      500  {object}  ErrorResponse
// @Router       /v1/devices/ [get]
func (h *DevicesHandler) GetDevices(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "Hello, World!"})
}

