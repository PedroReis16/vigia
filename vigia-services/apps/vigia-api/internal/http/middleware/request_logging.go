package middleware

import (
	"net/http"
	"strings"
	"time"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/logging"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// RequestContext generates or forwards X-Request-ID, stores a child logger on the Gin context
// and on context.Context, writes one structured access log after the handler chain, and sets
// the response header X-Request-ID for clients and proxies.
func RequestContext(base *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		rid := strings.TrimSpace(c.GetHeader(logging.HeaderRequestID))
		if rid == "" {
			rid = uuid.New().String()
		}

		reqLogger := base.With(zap.String("request_id", rid))
		c.Set(logging.ContextKeyRequestID, rid)
		c.Set(logging.ContextKeyLogger, reqLogger)
		c.Writer.Header().Set(logging.HeaderRequestID, rid)
		c.Request = c.Request.WithContext(logging.ContextWithRequestID(c.Request.Context(), rid))

		start := time.Now()
		c.Next()
		latency := time.Since(start)

		route := c.FullPath()
		if route == "" {
			route = c.Request.URL.Path
		}

		fields := []zap.Field{
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
			zap.String("route", route),
			zap.Int("status", c.Writer.Status()),
			zap.Duration("latency", latency),
			zap.Int64("latency_ms", latency.Milliseconds()),
			zap.String("client_ip", c.ClientIP()),
			zap.Int("response_size", c.Writer.Size()),
		}
		if len(c.Errors) > 0 {
			msgs := make([]string, 0, len(c.Errors))
			for _, e := range c.Errors {
				msgs = append(msgs, e.Error())
			}
			fields = append(fields, zap.Strings("error_messages", msgs))
		}

		status := c.Writer.Status()
		msg := "http_request"
		switch {
		case status >= http.StatusInternalServerError:
			reqLogger.Error(msg, fields...)
		case status >= http.StatusBadRequest:
			reqLogger.Warn(msg, fields...)
		default:
			reqLogger.Info(msg, fields...)
		}
	}
}
