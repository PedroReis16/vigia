package internal

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)


var RootCmd = &cobra.Command{
	Use:   "vigia-bootstrap",
	Short: "Ferramenta de linha de comando do projeto vigia bootstrap",
	Long: `Ferramenta de linha de comando do projeto vigia bootstrap`,
	SilenceUsage:  true,
	SilenceErrors: true,
	RunE: func(cmd *cobra.Command, args []string) error {
		return cmd.Help()
	},
}


func Execute() error {
	return RootCmd.Execute()
}

func init(){
	RootCmd.SetOut(os.Stdout)
	RootCmd.SetErr(os.Stderr)

	RootCmd.AddCommand(versionCmd)
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Versão do projeto",
	Long:  "Exibe a versão do projeto",
	Run: func(cmd *cobra.Command, args []string) {
		_, _ = fmt.Fprintln(cmd.OutOrStdout(), "vigia-bootstrap dev")
	},
}