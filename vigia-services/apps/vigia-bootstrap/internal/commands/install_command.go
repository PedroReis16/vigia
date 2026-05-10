package commands

import (
	"fmt"

	"github.com/spf13/cobra"
	 "github.com/PedroReis16/vigia/vigia-services/apps/vigia-bootstrap/internal"
)


var installCommand = &cobra.Command{
	Use:   "install",
	Short: "Instala o projeto",
	Long:  "Instala o projeto",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Instalando projeto...")
	},
}

func init(){
	internal.RootCmd.AddCommand(installCommand)
}