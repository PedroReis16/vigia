package bootstrap

import (
	"fmt"
	"strings"

	"gopkg.in/yaml.v3"
)

type composeTop struct {
	Services map[string]composeService `yaml:"services"`
}

type composeService struct {
	Image string `yaml:"image"`
}

// ImagesFromCompose extrai referências únicas do campo image: (ignora serviços sem image).
func ImagesFromCompose(composePath string) ([]string, error) {
	dataDir, err := assertComposeYAMLPath(composePath)
	if err != nil {
		return nil, err
	}
	data, err := readDataFile(dataDir, dataFileCompose)
	if err != nil {
		return nil, fmt.Errorf("ler compose: %w", err)
	}
	var top composeTop
	if err := yaml.Unmarshal(data, &top); err != nil {
		return nil, fmt.Errorf("parse compose: %w", err)
	}
	seen := make(map[string]struct{})
	var out []string
	for _, svc := range top.Services {
		img := strings.TrimSpace(svc.Image)
		if img == "" {
			continue
		}
		if _, ok := seen[img]; ok {
			continue
		}
		seen[img] = struct{}{}
		out = append(out, img)
	}
	return out, nil
}
