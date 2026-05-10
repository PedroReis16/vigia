package main

import (
	"log"
	"os"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	_ "github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal/commands"
)

func main() {
	if err := internal.Execute(); err != nil {
		log.Println(err)
		os.Exit(1)
	}
}
