package handlers_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/dtos"
	"github.com/gin-gonic/gin"
)

type stubVersionService struct {
	registerErr error
	getDTO      *dtos.VersionDTO
	getErr      error

	findDTO *dtos.VersionDTO
	findErr error
}

func (s *stubVersionService) RegisterNewVigiaVersion(*dtos.NewVersionDTO) error {
	return s.registerErr
}

func (s *stubVersionService) FindForUpdates(string) (*dtos.VersionDTO, error) {
	return s.findDTO, s.findErr
}

func (s *stubVersionService) GetVigiaVersion(string) (*dtos.VersionDTO, error) {
	return s.getDTO, s.getErr
}

func TestVersionHandler_RegisterNewVigiaVersion_badJSON(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewVersionHandler(&stubVersionService{})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPost, "/", bytes.NewReader([]byte(`{`)))

	h.RegisterNewVigiaVersion(c)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("status %d", w.Code)
	}
}

func TestVersionHandler_RegisterNewVigiaVersion_created(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewVersionHandler(&stubVersionService{})

	body := map[string]string{"version": "1.0.0"}
	buf, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPost, "/", bytes.NewReader(buf))
	c.Request.Header.Set("Content-Type", "application/json")

	h.RegisterNewVigiaVersion(c)
	if w.Code != http.StatusCreated {
		t.Fatalf("status %d body %s", w.Code, w.Body.String())
	}
}

func TestVersionHandler_RegisterNewVigiaVersion_serviceError(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewVersionHandler(&stubVersionService{registerErr: errors.New("fail")})

	buf, _ := json.Marshal(map[string]string{"version": "1.0.0"})
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPost, "/", bytes.NewReader(buf))
	c.Request.Header.Set("Content-Type", "application/json")

	h.RegisterNewVigiaVersion(c)
	if w.Code != http.StatusInternalServerError {
		t.Fatalf("status %d", w.Code)
	}
}

func TestVersionHandler_GetVigiaVersion_ok(t *testing.T) {
	gin.SetMode(gin.TestMode)
	dto := &dtos.VersionDTO{Version: "1", DownloadURL: "https://x"}
	h := handlers.NewVersionHandler(&stubVersionService{getDTO: dto})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/v1/1/download", nil)
	c.Params = gin.Params{{Key: "version", Value: "1"}}

	h.GetVigiaVersion(c)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d", w.Code)
	}
}

func TestVersionHandler_GetVigiaVersion_serviceError(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewVersionHandler(&stubVersionService{getErr: errors.New("boom")})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/", nil)
	c.Params = gin.Params{{Key: "version", Value: "v"}}

	h.GetVigiaVersion(c)
	if w.Code != http.StatusInternalServerError {
		t.Fatalf("status %d", w.Code)
	}
}

func TestVersionHandler_GetVigiaVersion_notFound(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewVersionHandler(&stubVersionService{getDTO: nil})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/", nil)
	c.Params = gin.Params{{Key: "version", Value: "v"}}

	h.GetVigiaVersion(c)
	if w.Code != http.StatusNotFound {
		t.Fatalf("status %d", w.Code)
	}
}

func TestVersionHandler_FindForUpdates_ok(t *testing.T) {
	gin.SetMode(gin.TestMode)
	dto := &dtos.VersionDTO{Version: "2.0.0", DownloadURL: "https://x"}
	h := handlers.NewVersionHandler(&stubVersionService{findDTO: dto})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/", nil)

	h.FindForUpdates(c)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d", w.Code)
	}
}

func TestVersionHandler_FindForUpdates_noContent(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewVersionHandler(&stubVersionService{findDTO: nil})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/?currentVersion=2.0.0", nil)

	h.FindForUpdates(c)
	if w.Code != http.StatusNoContent {
		t.Fatalf("status %d", w.Code)
	}
}

func TestVersionHandler_FindForUpdates_serviceError(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewVersionHandler(&stubVersionService{findErr: errors.New("db")})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/", nil)

	h.FindForUpdates(c)
	if w.Code != http.StatusInternalServerError {
		t.Fatalf("status %d", w.Code)
	}
}
