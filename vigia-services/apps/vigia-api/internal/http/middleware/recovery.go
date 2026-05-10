package middleware

import (
	"net/http"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/http/logging"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// ZapRecovery logs panics with the request-scoped logger (requires RequestContext earlier in the chain).
func ZapRecovery() gin.HandlerFunc {
	return gin.CustomRecovery(func(c *gin.Context, recovered interface{}) {
		logging.LoggerFromGin(c).Error("panic recovered",
			zap.Any("panic", recovered),
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
		)
		c.AbortWithStatus(http.StatusInternalServerError)
	})
}
