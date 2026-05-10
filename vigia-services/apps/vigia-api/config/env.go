package config

import (
	"os"
	"path/filepath"

	"github.com/joho/godotenv"
)

// LoadDotEnv loads the first existing .env file found by walking up from the
// current working directory and checking typical locations in this repo layout.
// Go does not read .env files by itself; without this, os.Getenv stays empty
// unless variables are exported in the shell, set by the IDE, or injected by Docker.
func LoadDotEnv() {
	wd, err := os.Getwd()
	if err != nil {
		return
	}
	for dir := wd; ; {
		candidates := []string{
			".env",
			filepath.Join("apps", "vigia-api", ".env"),
			filepath.Join("vigia-services", "apps", "vigia-api", ".env"),
		}
		for _, rel := range candidates {
			p := filepath.Join(dir, rel)
			fi, err := os.Stat(p)
			if err != nil || fi.IsDir() {
				continue
			}
			_ = godotenv.Load(p)
			return
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
}
