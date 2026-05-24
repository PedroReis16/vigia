package handlers

import (
	"context"
	"errors"
	"io"
	"net/http"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/logging"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/dtos"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// VersionHandlerService is the behavior required by VersionHandler (implemented by *services.VersionService).
type VersionHandlerService interface {
	RegisterNewVigiaVersion(ctx context.Context, version string, file io.Reader, size int64) error
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
	version := c.PostForm("version")
	if version == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "version é obrigatório"})
		return
	}

	fileHeader, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "file é obrigatório"})
		return
	}

	file, err := fileHeader.Open()
	if err != nil {
		_ = c.Error(err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "erro ao abrir arquivo enviado"})
		return
	}
	defer file.Close()

	if err := h.service.RegisterNewVigiaVersion(c.Request.Context(), version, file, fileHeader.Size); err != nil {
		_ = c.Error(err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	logging.LoggerFromGin(c).Info("versão registrada com sucesso",
		zap.String("event", "version_registered"),
		zap.String("version", version),
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
	versionParam := c.Param("version")
	version, err := h.service.GetVigiaVersion(versionParam)

	if err != nil {
		_ = c.Error(err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if version == nil {
		err := errors.New("versão não encontrada")
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
