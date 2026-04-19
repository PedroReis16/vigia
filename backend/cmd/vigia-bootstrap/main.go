package main

import (
	"os"
	vigiabootstrap "vigia/internal/vigia-bootstrap"
	"vigia/pkg/logger"

	"go.uber.org/zap"
)


func main(){
	log := logger.NewLogger("vigia-bootstrap")

	defer log.Sync()

	log.Info("Starting vigia-bootstrap")

	worker := vigiabootstrap.NewContainerWorker(log)

	if err := worker.Start(); err != nil{
		log.Error("Failed to start container observer worker", zap.String("error", err.Error()))
		os.Exit(1)	
	}

	log.Info("Container observer worker started successfully")
}