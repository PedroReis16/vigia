package vigiabootstrap

import (
	"bytes"
	"context"
	_ "embed"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
	"vigia/internal/vigia-bootstrap/models"
	"vigia/pkg/utils"

	"github.com/goccy/go-yaml"
	"go.uber.org/zap"
)


const (
	dockerRegistry = "registry-1.docker.io"
	authTokenURL   = "https://auth.docker.io/token"
	duration = 5 * time.Minute
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

	go func() {
		ticker := time.NewTicker(duration)
		defer ticker.Stop()

		checkAndApply := func() {
			c.Logger.Info("Checking for updates in services")
			hasUpdates, err := searchForUpdates(c.Logger, *composeFile)

			if err != nil {
				c.Logger.Error("Failed to search for updates in services", zap.Error(err))
				return
			}

			if !hasUpdates {
				return
			}

			c.Logger.Info("Updates found in services. Updating services")
			if err := applyComposeUpdates(context.Background(), *composeFile); err != nil {
				c.Logger.Error("Failed to apply compose updates", zap.Error(err))
			}
		}

		checkAndApply()
		for range ticker.C {
			checkAndApply()
		}
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

func searchForUpdates(logger *zap.Logger, composeFilePath string) (bool, error) {
	data, err := os.ReadFile(composeFilePath)

	if err != nil {
		return false, err
	}

	var cf models.ComposeFile
	if err := yaml.Unmarshal(data, &cf); err != nil {
		return false, err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	client := &http.Client{Timeout: 30 * time.Second}

	for serviceName, service := range cf.Services {
		ref := strings.TrimSpace(service.Image)

		if ref == "" {
			continue
		}

		repoPath, tag, err := splitRepositoryAndTag(ref)
		if err != nil {
			return false, err
		}

		remote, err := registryManifestDigest(ctx, client, repoPath, tag)
		if err != nil {
			return false, err
		}

		local, err := getLocalImageRepoDigest(ctx, ref)
		if err != nil {
			return false, err
		}

		if local == "" || !equalDigests(remote, local) {
			logger.Info("New version found for service",
				zap.String("service", serviceName),
				zap.String("remote", remote),
				zap.String("local", local),
			)
			return true, nil
		}
	}

	return false, nil
}

func splitRepositoryAndTag(ref string) (string, string, error) {
	imageRef := strings.TrimSpace(ref)

	if i := strings.Index(imageRef, "@"); i > 0 {
		return "", "", errors.New("Fixed image digest not supported: " + imageRef)
	}

	i := strings.LastIndex(imageRef, ":")
	if i < 0 {
		return normalizedHubRepository(imageRef), "latest", nil
	}
	candidateTag := imageRef[i+1:]

	if strings.Contains(candidateTag, "/") {
		return "", "", errors.New("Ambiguous image tag: " + imageRef)
	}
	repoOnly := imageRef[:i]
	return normalizedHubRepository(repoOnly), candidateTag, nil
}

func normalizedHubRepository(imageRef string) string {
	repo := strings.TrimPrefix(imageRef, "docker.io/")

	if !strings.Contains(repo, "/") {
		return "library/" + repo
	}
	return repo
}


func registryBearerToken(client *http.Client, repositoryPath string) (string, error) {
	scope := "repository:" + repositoryPath + ":pull"
	u, _ := url.Parse(authTokenURL)
	q := u.Query()
	q.Set("service", "registry.docker.io")
	q.Set("scope", scope)
	u.RawQuery = q.Encode()
	resp, err := client.Get(u.String())
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return "", fmt.Errorf("auth token %d: %s", resp.StatusCode, string(b))
	}
	var tr models.TokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&tr); err != nil {
		return "", err
	}
	if tr.Token != "" {
		return tr.Token, nil
	}
	if tr.AccessToken != "" {
		return tr.AccessToken, nil
	}
	return "", fmt.Errorf("empty token in auth response")
}

func registryManifestDigest(ctx context.Context, client *http.Client, repositoryPath, tag string) (string, error) {
	token, err := registryBearerToken(client, repositoryPath)
	if err != nil {
		return "", err
	}
	manifestURL := fmt.Sprintf("https://%s/v2/%s/manifests/%s",
		dockerRegistry, repositoryPath, url.PathEscape(tag))
	req, err := http.NewRequestWithContext(ctx, http.MethodHead, manifestURL, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	// Pedir lista (multi-arch) primeiro; o registry devolve digest do manifest negociado.
	req.Header.Set("Accept", "application/vnd.docker.distribution.manifest.list.v2+json")
	req.Header.Set("Accept", "application/vnd.docker.distribution.manifest.v2+json")
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, io.LimitReader(resp.Body, 8192))
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return "", fmt.Errorf("HEAD manifest %d: %s", resp.StatusCode, string(b))
	}
	d := resp.Header.Get("Docker-Content-Digest")
	if d == "" {
		return "", fmt.Errorf("missing Docker-Content-Digest header")
	}
	return d, nil
}

func getLocalImageRepoDigest(ctx context.Context, imageRef string) (string, error) {
	cmd := exec.CommandContext(ctx, "docker", "image", "inspect",
		"--format", "{{index .RepoDigests 0}}", imageRef)
	out, err := cmd.CombinedOutput()
	s := strings.TrimSpace(string(out))
	if err != nil {
		if dockerInspectOutputMeansNoLocalImage(string(out)) {
			return "", nil
		}
		return "", fmt.Errorf("%w: %s", err, strings.TrimSpace(string(out)))
	}
	if s == "" {
		return "", nil
	}
	// Formato: repo@sha256:...
	if i := strings.Index(s, "@"); i >= 0 {
		return s[i+1:], nil
	}
	return s, nil
}

// dockerInspectOutputMeansNoLocalImage recognizes common docker image inspect failures
// when the reference is not present locally (first pull, typo, etc.). Messages differ by
// locale and Docker version ("No such object" vs "No such image", etc.).
func dockerInspectOutputMeansNoLocalImage(combinedOutput string) bool {
	s := strings.ToLower(combinedOutput)
	return strings.Contains(s, "no such object") ||
		strings.Contains(s, "no such image") ||
		strings.Contains(s, "could not find the image")
}


func equalDigests(a, b string) bool {
	return strings.EqualFold(trimSHA(a), trimSHA(b))
}

func trimSHA(digest string) string {
	d := strings.TrimSpace(digest)
	d = strings.TrimPrefix(d, "sha256:")
	return d
}

func applyComposeUpdates(ctx context.Context, composeFilePath string) error {
	composeFilePath = filepath.Clean(composeFilePath)
	dir := filepath.Dir(composeFilePath)
	pull := exec.CommandContext(ctx, "docker", "compose", "-f", composeFilePath, "pull")
	pull.Dir = dir
	if out, err := pull.CombinedOutput(); err != nil {
		return fmt.Errorf("docker compose pull: %w\n%s", err, out)
	}
	up := exec.CommandContext(ctx, "docker", "compose", "-f", composeFilePath, "up", "-d")
	up.Dir = dir
	if out, err := up.CombinedOutput(); err != nil {
		return fmt.Errorf("docker compose up: %w\n%s", err, out)
	}
	return nil
}
