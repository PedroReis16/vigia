package utils

import (
	"os"
	"path/filepath"
	"strings"
)

func GetCompletePath(path string) string{
	if strings.HasPrefix(path, "~"){
		home := getHomePath()
		if path == "~"{
			return home
		}
		return filepath.Join(home, strings.TrimPrefix(path, "~/"))
	}
	return path
}

func getHomePath() string{
	home, err := os.UserHomeDir()

	if err != nil{
		return "/"
	}
	return home
}