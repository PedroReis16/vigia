package main

import (
	"fmt"

	"github.com/spf13/cobra"
)

func main() {
	var rootCommand = &cobra.Command{}

	var projectName, projectPath string

	var cmd = &cobra.Command{
		Use:   "create",
		Short: "Create boilerplate for a new project",
		Run: func(cmd *cobra.Command, args []string) {
			// validations
			if projectName == "" {
				fmt.Println("You must supply a project name.")
				return
			}
			if projectPath == "" {
				fmt.Println("You must supply a project path.")
				return
			}
			fmt.Println("Creating project...")
		},
	}

	cmd.Flags().StringVarP(&projectName, "name", "n", "", "Name of the project")
	cmd.Flags().StringVarP(&projectPath, "path", "p", "", "Path where the project will be created")

	rootCommand.AddCommand(cmd)
	rootCommand.Execute()
}
