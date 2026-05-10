package api_test

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/api"
)

func TestClient_FindForUpdates_200(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/devices/version/find-for-updates" {
			t.Fatalf("path: %s", r.URL.Path)
		}
		if r.URL.Query().Get("currentVersion") != "1.0.0" {
			t.Fatalf("currentVersion query: %q", r.URL.Query().Get("currentVersion"))
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"version":"2.0.0","download_url":"https://example.org/bin"}`))
	}))
	defer srv.Close()

	c, err := api.NewClient(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	dto, err := c.FindForUpdates(context.Background(), "1.0.0")
	if err != nil {
		t.Fatal(err)
	}
	if dto.Version != "2.0.0" || dto.DownloadURL != "https://example.org/bin" {
		t.Fatalf("dto: %+v", dto)
	}
}

func TestClient_FindForUpdates_204(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c, err := api.NewClient(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	dto, err := c.FindForUpdates(context.Background(), "9.9.9")
	if err != nil {
		t.Fatal(err)
	}
	if dto != nil {
		t.Fatalf("want nil dto, got %+v", dto)
	}
}

func TestClient_FindForUpdates_500_JSONError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_, _ = w.Write([]byte(`{"error":"nenhuma versão disponível"}`))
	}))
	defer srv.Close()

	c, err := api.NewClient(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	_, err = c.FindForUpdates(context.Background(), "")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestNewClient_emptyBaseURL(t *testing.T) {
	_, err := api.NewClient("  ")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestClient_FindForUpdates_nilReceiver(t *testing.T) {
	var c *api.Client
	_, err := c.FindForUpdates(context.Background(), "")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestClient_FindForUpdates_HTTPNil(t *testing.T) {
	c := &api.Client{BaseURL: "http://localhost", HTTP: nil}
	_, err := c.FindForUpdates(context.Background(), "")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestClient_FindForUpdates_200_badJSON(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`not-json`))
	}))
	defer srv.Close()

	c, err := api.NewClient(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	_, err = c.FindForUpdates(context.Background(), "")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestClient_FindForUpdates_200_missingDownloadURL(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"version":"1.0.0"}`))
	}))
	defer srv.Close()

	c, err := api.NewClient(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	_, err = c.FindForUpdates(context.Background(), "")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestClient_FindForUpdates_404_plainBody(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		_, _ = w.Write([]byte("gone"))
	}))
	defer srv.Close()

	c, err := api.NewClient(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	_, err = c.FindForUpdates(context.Background(), "")
	if err == nil {
		t.Fatal("expected error")
	}
}
