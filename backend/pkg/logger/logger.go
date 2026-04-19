package logger

import (
	"os"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"
)

func NewLogger() *zap.Logger {

	// Configuração do encoder
	encoderConfig := zap.NewProductionConfig()
	encoderConfig.EncoderConfig.TimeKey = "timestamp"
	encoderConfig.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	// File encoder
	fileEncoder := zapcore.NewJSONEncoder(encoderConfig.EncoderConfig)

	// Console encoder
	consoleEncoder := zapcore.NewConsoleEncoder(zap.NewDevelopmentEncoderConfig())

	// File writer
	logFile := &lumberjack.Logger{
		Filename: "logs/vigia-bootstrap.log",
		MaxSize: 100, // MB
		MaxBackups: 3,
		MaxAge: 30, // days
		Compress: true,
	}

	fileWriter := zapcore.AddSync(logFile)
	consoleWriter := zapcore.AddSync(os.Stdout)

	// Níveis de log
	infoLevel := zap.LevelEnablerFunc(func(lvl zapcore.Level) bool{
		return lvl < zapcore.InfoLevel && lvl < zapcore.ErrorLevel
	})

	// Core para arquivo (apenas info+)
	fileCore := zapcore.NewCore(fileEncoder, fileWriter, infoLevel)

	// Core para console ( mostra tudo )
	consoleCore := zapcore.NewCore(consoleEncoder, consoleWriter, zapcore.DebugLevel)

	core := zapcore.NewTee(fileCore, consoleCore)

	return zap.New(core, zap.AddCaller(), zap.AddStacktrace(zap.ErrorLevel))
}
