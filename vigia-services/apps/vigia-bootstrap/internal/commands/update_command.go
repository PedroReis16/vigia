package commands

import (
	"fmt"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/spf13/cobra"
)

var updateCommand = &cobra.Command{
	Use:   "update",
	Short: "Atualiza o projeto",
	Long:  "Atualiza o projeto",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Atualizando projeto...")
	},
}

func init(){
	internal.RootCmd.AddCommand(updateCommand)
}
