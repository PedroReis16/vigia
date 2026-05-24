package api

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

const findForUpdatesPath = "/v1/devices/version/find-for-updates"

// Client calls vigia-api version endpoints.
type Client struct {
	BaseURL string
	HTTP    *http.Client
}

// NewClient returns a client with BaseURL normalized (no trailing slash).
func NewClient(baseURL string) (*Client, error) {
	baseURL = strings.TrimSpace(baseURL)
	baseURL = strings.TrimSuffix(baseURL, "/")
	if baseURL == "" {
		return nil, fmt.Errorf("api base URL is empty")
	}
	return &Client{
		BaseURL: baseURL,
		HTTP: &http.Client{
			Timeout: 2 * time.Minute,
		},
	}, nil
}

// FindForUpdates calls GET /v1/devices/version/find-for-updates.
// 204 No Content means no newer version (nil, nil).
// 200 OK returns version metadata including download_url.
func (c *Client) FindForUpdates(ctx context.Context, currentVersion string) (*VersionDTO, error) {
	if c == nil || c.HTTP == nil {
		return nil, fmt.Errorf("api client is not configured")
	}
	u, err := url.Parse(c.BaseURL + findForUpdatesPath)
	if err != nil {
		return nil, err
	}
	q := u.Query()
	q.Set("currentVersion", currentVersion)
	u.RawQuery = q.Encode()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u.String(), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.HTTP.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNoContent {
		return nil, nil
	}

	body, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		var er errorResponseBody
		if json.Unmarshal(body, &er) == nil && er.Error != "" {
			return nil, fmt.Errorf("api error (%d): %s", resp.StatusCode, er.Error)
		}
		return nil, fmt.Errorf("api returned status %d", resp.StatusCode)
	}

	var dto VersionDTO
	if err := json.Unmarshal(body, &dto); err != nil {
		return nil, fmt.Errorf("decode version response: %w", err)
	}
	if dto.DownloadURL == "" {
		return nil, fmt.Errorf("api response missing download_url")
	}
	return &dto, nil
}
