package main

import (
	"fmt"
	"vigia/pkg/logger"
)


func main(){
	log := logger.NewLogger("vigia-bootstrap")

	defer log.Sync()

	log.Info("Starting vigia-bootstrap")

	fmt.Println("Hello, World!")
}