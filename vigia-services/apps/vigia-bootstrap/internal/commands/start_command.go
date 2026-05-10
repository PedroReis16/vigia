package commands

import (
	"fmt"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/spf13/cobra"
)

var serviceInitCommand = &cobra.Command{
	Use:   "service-init",
	Short: "Inicializa o serviço",
	Long:  "Inicializa o serviço",
	Run: func(cmd *cobra.Command, args []string) {
		fmt	.Println("Inicializando serviço...")
	},
}

func init(){
	internal.RootCmd.AddCommand(serviceInitCommand)
}

