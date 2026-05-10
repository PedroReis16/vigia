package api

// VersionDTO matches vigia-api JSON for version metadata and presigned download URL.
type VersionDTO struct {
	Version     string `json:"version"`
	DownloadURL string `json:"download_url"`
}

type errorResponseBody struct {
	Error string `json:"error"`
}
