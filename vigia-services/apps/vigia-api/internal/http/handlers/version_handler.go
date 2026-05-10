package handlers

import (
	"errors"
	"net/http"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/logging"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/dtos"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// VersionHandlerService is the behavior required by VersionHandler (implemented by *services.VersionService).
type VersionHandlerService interface {
	RegisterNewVigiaVersion(*dtos.NewVersionDTO) error
	FindForUpdates(currentVersion string) (*dtos.VersionDTO, error)
	GetVigiaVersion(version string) (*dtos.VersionDTO, error)
}

type VersionHandler struct {
	service VersionHandlerService
}

func NewVersionHandler(service VersionHandlerService) *VersionHandler {
	return &VersionHandler{service: service}
}

func (h *VersionHandler) RegisterNewVigiaVersion(c *gin.Context) {
	// Registra uma nova versão do Vigia para o dispositivo
	var newVersionDTO dtos.NewVersionDTO
	if err := c.ShouldBindJSON(&newVersionDTO); err != nil {
		_ = c.Error(err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err := h.service.RegisterNewVigiaVersion(&newVersionDTO)
	if err != nil {
		_ = c.Error(err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	logging.LoggerFromGin(c).Info("versão registrada com sucesso",
		zap.String("event", "version_registered"),
		zap.String("version", newVersionDTO.Version),
	)

	c.JSON(http.StatusCreated, gin.H{"message": "Versão registrada com sucesso"})
}

func (h *VersionHandler) FindForUpdates(c *gin.Context) {
	currentVersion := c.Query("currentVersion")
	dto, err := h.service.FindForUpdates(currentVersion)
	if err != nil {
		_ = c.Error(err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if dto == nil {
		c.AbortWithStatus(http.StatusNoContent)
		return
	}

	logging.LoggerFromGin(c).Info("atualização disponível ou última versão consultada",
		zap.String("event", "version_find_for_updates"),
		zap.String("current_version_query", currentVersion),
		zap.String("offered_version", dto.Version),
	)

	c.JSON(http.StatusOK, dto)
}

func (h *VersionHandler) GetVigiaVersion(c *gin.Context) {
	// Retorna a versão do vigia para o vigia

	versionParam := c.Param("version")
	version, err := h.service.GetVigiaVersion(versionParam)

	if err != nil {
		_ = c.Error(err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if version == nil {
		err := errors.New("Versão não encontrada")
		_ = c.Error(err)
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	logging.LoggerFromGin(c).Info("metadados da versão obtidos para download",
		zap.String("event", "version_download_metadata"),
		zap.String("version", version.Version),
	)

	c.JSON(http.StatusOK, version)
}
