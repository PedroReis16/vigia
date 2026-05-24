package services

import (
	"context"
	"errors"
	"fmt"
	"io"
	"strings"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/dtos"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/entities"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/repositories"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/repositories/cache"
	"golang.org/x/mod/semver"
	"gorm.io/gorm"
)

// versionURLCache exposes URL caching used by VersionService (implemented by *cache.VersionUrlRepositoryCache).
type versionURLCache interface {
	GetVersionUrl(version string) (*string, error)
	SetVersionUrl(version string, url string) error
}

// versionStore persists and reads version rows (implemented by *repositories.VersionRepository).
type versionStore interface {
	FindVersion(version string) (*entities.Version, error)
	FindLatestVersion() (*entities.Version, error)
	RegisterVersion(newVersion *entities.Version) error
}

// bucketProvider uploads and generates download URLs (implemented by *BucketService).
type bucketProvider interface {
	GetVersionPreSignedUrl(version string) (*string, error)
	UploadVersion(ctx context.Context, version string, reader io.Reader, size int64) error
}

type VersionService struct {
	versionUrlRepositoryCache versionURLCache
	versionRepository         versionStore
	bucketService             bucketProvider
}

func NewVersionService(
	versionUrlRepositoryCache *cache.VersionUrlRepositoryCache,
	versionRepository *repositories.VersionRepository,
	bucketService *BucketService) *VersionService {

	return &VersionService{
		versionUrlRepositoryCache: versionUrlRepositoryCache,
		versionRepository:         versionRepository,
		bucketService:             bucketService,
	}
}

func (s *VersionService) RegisterNewVigiaVersion(ctx context.Context, version string, file io.Reader, size int64) error {
	if err := s.bucketService.UploadVersion(ctx, version, file, size); err != nil {
		return fmt.Errorf("upload version to bucket: %w", err)
	}

	newVersion := (&entities.Version{}).NewVersion()
	newVersion.Version = version
	newVersion.IsLatest = true

	return s.versionRepository.RegisterVersion(newVersion)
}

// FindForUpdates returns download metadata for the newest published version.
// currentVersion empty: always returns the latest build.
// currentVersion set: returns the latest only if it is newer than currentVersion (semver); if already up to date, returns (nil, nil).
func (s *VersionService) FindForUpdates(currentVersion string) (*dtos.VersionDTO, error) {
	latest, err := s.versionRepository.FindLatestVersion()
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, errors.New("nenhuma versão disponível")
		}
		return nil, err
	}

	currentVersion = strings.TrimSpace(currentVersion)
	if currentVersion == "" {
		return s.GetVigiaVersion(latest.Version)
	}

	if versionIsUpToDate(currentVersion, latest.Version) {
		return nil, nil
	}
	return s.GetVigiaVersion(latest.Version)
}

func versionIsUpToDate(current, latest string) bool {
	c := semverCanonical(current)
	l := semverCanonical(latest)
	if semver.IsValid(c) && semver.IsValid(l) {
		return semver.Compare(c, l) >= 0
	}
	return strings.EqualFold(strings.TrimSpace(current), strings.TrimSpace(latest))
}

func semverCanonical(v string) string {
	v = strings.TrimSpace(v)
	if v == "" {
		return ""
	}
	if !strings.HasPrefix(v, "v") {
		return "v" + v
	}
	return v
}

func (s *VersionService) GetVigiaVersion(version string) (*dtos.VersionDTO, error) {
	url, _ := s.versionUrlRepositoryCache.GetVersionUrl(version)

	if url == nil {
		result, err := s.versionRepository.FindVersion(version)
		if err != nil || result == nil {
			return nil, errors.New("version not found")
		}

		url, err = s.bucketService.GetVersionPreSignedUrl(result.Version)
		if err != nil {
			return nil, err
		}

		if err := s.versionUrlRepositoryCache.SetVersionUrl(result.Version, *url); err != nil {
			return nil, fmt.Errorf("cache version URL: %w", err)
		}
		return &dtos.VersionDTO{
			Version:     result.Version,
			DownloadURL: *url,
		}, nil
	}

	return &dtos.VersionDTO{
		Version:     version,
		DownloadURL: *url,
	}, nil
}
