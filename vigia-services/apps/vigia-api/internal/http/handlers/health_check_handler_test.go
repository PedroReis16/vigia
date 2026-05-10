package handlers_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/handlers"
	"github.com/gin-gonic/gin"
)

func TestHealthCheckHandler_Handle(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := handlers.NewHealthCheckHandler()

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/health", nil)

	h.Handle(c)
	if w.Code != http.StatusOK {
		t.Fatalf("status %d", w.Code)
	}

	var body handlers.HealthCheckResponse
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("json: %v", err)
	}
	if body.Message == "" {
		t.Fatal("empty message")
	}
}
