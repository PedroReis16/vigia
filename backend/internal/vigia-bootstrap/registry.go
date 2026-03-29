package bootstrap

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// RegistryManifestDigest obtém o digest da manifest (Docker Hub / OCI registry v2).
// Referências fixas por digest (@sha256:...) não são consultadas.
func RegistryManifestDigest(ctx context.Context, imageRef string) (string, error) {
	repo, tag, pinned := parseRepoTag(imageRef)
	if pinned {
		return "", fmt.Errorf("imagem já fixada por digest: %s", imageRef)
	}
	if tag == "" {
		tag = "latest"
	}

	token, err := dockerHubToken(ctx, repo)
	if err != nil {
		return "", err
	}

	manifestURL := fmt.Sprintf("https://registry-1.docker.io/v2/%s/manifests/%s", repo, url.PathEscape(tag))
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, manifestURL, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", strings.Join([]string{
		"application/vnd.docker.distribution.manifest.list.v2+json",
		"application/vnd.docker.distribution.manifest.v2+json",
		"application/vnd.oci.image.index.v1+json",
		"application/vnd.oci.image.manifest.v1+json",
	}, ", "))

	client := &http.Client{Timeout: 2 * time.Minute}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("registry GET: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return "", fmt.Errorf("registry %s: %s — %s", manifestURL, resp.Status, strings.TrimSpace(string(b)))
	}
	digest := resp.Header.Get("Docker-Content-Digest")
	if digest == "" {
		return "", fmt.Errorf("cabeçalho Docker-Content-Digest vazio para %s", imageRef)
	}
	return digest, nil
}

func dockerHubToken(ctx context.Context, repository string) (string, error) {
	scope := "repository:" + repository + ":pull"
	u := "https://auth.docker.io/token?service=registry.docker.io&scope=" + url.QueryEscape(scope)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return "", err
	}
	client := &http.Client{Timeout: 1 * time.Minute}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("token: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
		return "", fmt.Errorf("token %s: %s", resp.Status, strings.TrimSpace(string(b)))
	}
	var tr struct {
		Token string `json:"token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&tr); err != nil {
		return "", fmt.Errorf("decode token: %w", err)
	}
	if tr.Token == "" {
		return "", fmt.Errorf("token vazio")
	}
	return tr.Token, nil
}

// parseRepoTag devolve repositório no formato registry (ex.: library/nginx) e tag.
func parseRepoTag(ref string) (repository, tag string, pinnedByDigest bool) {
	if i := strings.Index(ref, "@"); i >= 0 {
		return ref[:i], "", true
	}
	tag = "latest"
	slash := strings.LastIndex(ref, "/")
	var tail string
	if slash < 0 {
		tail = ref
	} else {
		tail = ref[slash+1:]
	}
	if idx := strings.LastIndex(tail, ":"); idx >= 0 {
		repo := ref[:slash+1+idx]
		if slash < 0 && !strings.Contains(repo, "/") {
			repo = "library/" + repo
		}
		return repo, tail[idx+1:], false
	}
	if slash < 0 {
		return "library/" + ref, tag, false
	}
	return ref, tag, false
}
