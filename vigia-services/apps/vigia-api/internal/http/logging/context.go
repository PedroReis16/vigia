package logging

import (
	"context"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

type ctxKeyRequestID struct{}

const (
	ContextKeyLogger    = "zap_logger"
	ContextKeyRequestID = "request_id"
	HeaderRequestID     = "X-Request-ID"
)

// LoggerFromGin returns the request-scoped logger (includes request_id) or a no-op logger.
func LoggerFromGin(c *gin.Context) *zap.Logger {
	if v, ok := c.Get(ContextKeyLogger); ok {
		if l, ok := v.(*zap.Logger); ok {
			return l
		}
	}
	return zap.NewNop()
}

// RequestIDFromGin returns the request id for this HTTP call, if middleware ran.
func RequestIDFromGin(c *gin.Context) string {
	if v, ok := c.Get(ContextKeyRequestID); ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

// ContextWithRequestID attaches the request id for downstream layers that only see context.Context.
func ContextWithRequestID(ctx context.Context, id string) context.Context {
	if id == "" {
		return ctx
	}
	return context.WithValue(ctx, ctxKeyRequestID{}, id)
}

// RequestIDFromContext reads the id set by ContextWithRequestID.
func RequestIDFromContext(ctx context.Context) string {
	if ctx == nil {
		return ""
	}
	if v := ctx.Value(ctxKeyRequestID{}); v != nil {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}
