package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
)

func TestHealthEndpoint(t *testing.T) {
	router := newRouter()

	req := httptest.NewRequest(http.MethodGet, "/gerenciamento-dispositivos/health", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status inesperado: got=%d want=%d", rec.Code, http.StatusOK)
	}

	var body struct {
		Message string `json:"message"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
		t.Fatalf("falha ao decodificar resposta: %v", err)
	}
	if body.Message == "" {
		t.Fatal("mensagem de health não pode ser vazia")
	}
}

func TestResolveAPIAddr(t *testing.T) {
	const envKey = "VIGIA_API_ADDR"
	oldValue, hadOld := os.LookupEnv(envKey)
	t.Cleanup(func() {
		if hadOld {
			_ = os.Setenv(envKey, oldValue)
			return
		}
		_ = os.Unsetenv(envKey)
	})

	_ = os.Unsetenv(envKey)
	if got, want := resolveAPIAddr(), "127.0.0.1:8000"; got != want {
		t.Fatalf("endereço default inválido: got=%q want=%q", got, want)
	}

	_ = os.Setenv(envKey, " 0.0.0.0:9999 ")
	if got, want := resolveAPIAddr(), "0.0.0.0:9999"; got != want {
		t.Fatalf("endereço via env inválido: got=%q want=%q", got, want)
	}
}
