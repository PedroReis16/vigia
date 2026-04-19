package vigiabootstrap

import (
	"bytes"
	_ "embed"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"vigia/pkg/utils"

	"go.uber.org/zap"
)

//go:embed config/docker-compose.yaml
var embeddedComposeFile []byte

//go:embed config/base.env
var embeddedBaseEnv []byte

type ContainerWorker struct {
	Logger *zap.Logger
}

func NewContainerWorker(logger *zap.Logger) *ContainerWorker {
	return &ContainerWorker{
		Logger: logger,
	}
}

func (c *ContainerWorker) Start() error {
	c.Logger.Info("Starting container observer worker")

	composeFile, err := loadComposeContainers(c.Logger)

	if err != nil {
		c.Logger.Error("Failed to load compose containers", zap.Error(err))
		return err
	}

	fmt.Println(composeFile)

	go func() {

	}()

	return nil
}

func loadComposeContainers(logger *zap.Logger) (*string, error) {
	composeFile := "~/vigia/compose/docker-compose.yaml"

	composeFile = utils.GetCompletePath(composeFile)

	envFile := "~/vigia/compose/default.env"
	envFile = utils.GetCompletePath(envFile)

	byteFile := []byte(embeddedBaseEnv)

	if err := ensureFileExists(logger, composeFile, embeddedComposeFile); err != nil {
		return nil, err
	}

	if err := ensureFileExists(logger, envFile, byteFile); err != nil {
		return nil, err
	}

	return &composeFile, nil
}

func ensureFileExists(logger *zap.Logger, filePath string, fileContent []byte) error {
	_, err := os.Stat(filePath)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			logger.Info("File not found. Creating file")
			if err := os.MkdirAll(filepath.Dir(filePath), 0755); err != nil {
				return err
			}
			if err := os.WriteFile(filePath, fileContent, 0644); err != nil {
				return err
			}
			return nil
		}
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		return err
	}
	if !bytes.Equal(content, fileContent) {
		logger.Info("File content differs from embedded content. Updating file.")
		if err := os.WriteFile(filePath, fileContent, 0644); err != nil {
			return err
		}
	}
	
	return nil
}
