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

// RegisterNewVigiaVersion godoc
// @Summary      Registrar nova versão do Vigia
// @Description  Faz upload de um bundle do agente fall-detection e registra uma nova versão no catálogo.
// @Tags         versions
// @Accept       multipart/form-data
// @Produce      json
// @Param        version  formData  string  true  "Identificador semântico da versão (ex.: 1.2.3)"
// @Param        file     formData  file    true  "Bundle compactado da versão"
// @Success      201  {object}  MessageResponse
// @Failure      400  {object}  ErrorResponse
// @Failure      500  {object}  ErrorResponse
// @Router       /v1/devices/version/register [post]
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

// FindForUpdates godoc
// @Summary      Buscar atualização disponível
// @Description  Retorna metadados da versão mais recente publicada. Quando `currentVersion` é informada via query, responde 204 caso o dispositivo já esteja na versão mais recente.
// @Tags         versions
// @Produce      json
// @Param        currentVersion  query     string  false  "Versão atualmente instalada no dispositivo (semver)"
// @Success      200  {object}  dtos.VersionDTO
// @Success      204  "Dispositivo já está na versão mais recente"
// @Failure      500  {object}  ErrorResponse
// @Router       /v1/devices/version/find-for-updates [get]
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

// GetVigiaVersion godoc
// @Summary      Obter metadados de uma versão
// @Description  Retorna a URL de download pré-assinada para a versão informada.
// @Tags         versions
// @Produce      json
// @Param        version  path      string  true  "Versão alvo (semver)"
// @Success      200  {object}  dtos.VersionDTO
// @Failure      404  {object}  ErrorResponse
// @Failure      500  {object}  ErrorResponse
// @Router       /v1/devices/version/{version}/download [get]
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
