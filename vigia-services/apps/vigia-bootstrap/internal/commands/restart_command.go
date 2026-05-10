package commands

import (
	"fmt"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/spf13/cobra"
)

var restartCommand = &cobra.Command{
	Use:   "restart",
	Short: "Reinicia o projeto",
	Long:  "Reinicia o projeto",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Reiniciando projeto...")
	},
}

func init(){
	internal.RootCmd.AddCommand(restartCommand)
}