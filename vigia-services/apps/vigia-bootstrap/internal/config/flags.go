package config

import (
	"os"
	"strings"
)

// APIBaseURL, DataDir, SystemdUnit are bound to cobra persistent flags on the root command.
var (
	APIBaseURL  string
	DataDir     string
	SystemdUnit string
)

// ResolvedAPIBaseURL returns the API base URL from flags or VIGIA_API_BASE_URL.
func ResolvedAPIBaseURL() string {
	v := strings.TrimSpace(APIBaseURL)
	if v == "" {
		v = strings.TrimSpace(os.Getenv("VIGIA_API_BASE_URL"))
	}
	return strings.TrimSuffix(v, "/")
}

// ResolvedSystemdUnit returns the unit name (without requiring .service suffix).
func ResolvedSystemdUnit() string {
	v := strings.TrimSpace(SystemdUnit)
	if v != "" {
		return v
	}
	if v = strings.TrimSpace(os.Getenv("VIGIA_SYSTEMD_UNIT")); v != "" {
		return v
	}
	return "fall-detection"
}
