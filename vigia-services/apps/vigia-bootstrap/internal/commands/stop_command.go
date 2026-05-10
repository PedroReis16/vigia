package commands

import (
	"fmt"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
	"github.com/spf13/cobra"
)

var stopCommand = &cobra.Command{
	Use:   "stop",
	Short: "Para o projeto",
	Long:  "Para o projeto",	
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Parando projeto...")
	},
}

func init(){
	internal.RootCmd.AddCommand(stopCommand)
}