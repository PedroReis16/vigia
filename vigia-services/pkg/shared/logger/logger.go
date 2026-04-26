package logger

import (
	"os"
	"path/filepath"
	"strings"
	"github.com/PedroReis16/vigia/vigia-services/pkg/shared/utils"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"
)

func NewLogger(projectName string) *zap.Logger {

	// Configuração do encoder
	encoderConfig := zap.NewProductionConfig()
	encoderConfig.EncoderConfig.TimeKey = "timestamp"
	encoderConfig.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	// File encoder
	fileEncoder := zapcore.NewJSONEncoder(encoderConfig.EncoderConfig)

	// Console encoder
	consoleEncoder := zapcore.NewConsoleEncoder(zap.NewDevelopmentEncoderConfig())

	logPath := createFilePath(projectName)

	// File writer
	logFile := &lumberjack.Logger{
		Filename: logPath,
		MaxSize: 10, // MB
		MaxBackups: 3,
		MaxAge: 7, // days
		Compress: true,
	}

	fileWriter := zapcore.AddSync(logFile)
	// stderr under systemd tends to reach journal reliably; stdout without TTY may be fully buffered so logs appear late or never.
	consoleWriter := zapcore.AddSync(os.Stderr)

	// Níveis de log
	infoLevel := zap.LevelEnablerFunc(func(lvl zapcore.Level) bool{
		return lvl >= zapcore.InfoLevel && lvl < zapcore.PanicLevel
	})

	// Core para arquivo (apenas info+)
	fileCore := zapcore.NewCore(fileEncoder, fileWriter, infoLevel)

	// Core para console ( mostra tudo )
	consoleCore := zapcore.NewCore(consoleEncoder, consoleWriter, zapcore.DebugLevel)

	core := zapcore.NewTee(fileCore, consoleCore)

	return zap.New(core, zap.AddCaller(), zap.AddStacktrace(zap.PanicLevel))
}

func createFilePath(projectName string) string {
	var logPath string
	if logDir := strings.TrimSpace(os.Getenv("VIGIA_LOG_DIR")); logDir != "" {
		logPath = filepath.Join(filepath.Clean(logDir), projectName, projectName+".log")
	} else {
		logPath = "~/vigia/logs/" + projectName + "/" + projectName + ".log"
		logPath = utils.GetCompletePath(logPath)
	}

	parent := filepath.Dir(logPath)
	if err := os.MkdirAll(parent, 0755); err != nil {
		panic(err)
	}

	return logPath
}