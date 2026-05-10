package logging

import (
	"context"
	"testing"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func TestLoggerFromGin_withLogger(t *testing.T) {
	gin.SetMode(gin.TestMode)
	c, _ := gin.CreateTestContext(nil)
	log := zap.NewNop()
	c.Set(ContextKeyLogger, log)

	if LoggerFromGin(c) != log {
		t.Fatal("expected same logger instance")
	}
}

func TestLoggerFromGin_fallbackNop(t *testing.T) {
	gin.SetMode(gin.TestMode)
	c, _ := gin.CreateTestContext(nil)
	l := LoggerFromGin(c)
	if l == nil {
		t.Fatal("nil logger")
	}
}

func TestRequestIDFromGin(t *testing.T) {
	gin.SetMode(gin.TestMode)
	c, _ := gin.CreateTestContext(nil)
	c.Set(ContextKeyRequestID, "abc")

	if RequestIDFromGin(c) != "abc" {
		t.Fatal(RequestIDFromGin(c))
	}
}

func TestContextWithRequestID(t *testing.T) {
	ctx := ContextWithRequestID(context.Background(), "rid")
	if RequestIDFromContext(ctx) != "rid" {
		t.Fatalf("got %q", RequestIDFromContext(ctx))
	}
}

func TestContextWithRequestID_emptyNoOp(t *testing.T) {
	base := context.Background()
	ctx := ContextWithRequestID(base, "")
	if ctx != base {
		t.Fatal("expected same context when id empty")
	}
}

func TestRequestIDFromContext_nil(t *testing.T) {
	if RequestIDFromContext(nil) != "" {
		t.Fatal("want empty")
	}
}
