package handlers_test

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/services"
	"github.com/gin-gonic/gin"
)

func TestDevicesHandler_RegisterUserDevice(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewDevicesHandler(&services.DeviceService{})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPost, "/register", nil)

	h.RegisterUserDevice(c)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d", w.Code)
	}
}

func TestDevicesHandler_GetDevices(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewDevicesHandler(&services.DeviceService{})

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/", nil)

	h.GetDevices(c)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d", w.Code)
	}
}
