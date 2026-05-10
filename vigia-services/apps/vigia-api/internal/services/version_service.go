package services

import (
	"errors"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/dtos"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/entities"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/repositories"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/repositories/cache"
)

type VersionService struct {
	versionUrlRepositoryCache *cache.VersionUrlRepositoryCache
	versionRepository         *repositories.VersionRepository
	bucketService             *BucketService
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

func (s *VersionService) RegisterNewVigiaVersion(newVersionDTO *dtos.NewVersionDTO) error {

	newVersion := (&entities.Version{}).NewVersion()
	newVersion.Version = newVersionDTO.Version
	newVersion.IsLatest = true

	err := s.versionRepository.RegisterVersion(newVersion)
	if err != nil {
		return err
	}

	return nil
}

func (s *VersionService) FindForUpdates(currentVersion string) (*string, error) {

	return nil, nil
}

func (s *VersionService) GetVigiaVersion(version string) (*dtos.VersionDTO, error) {
	// Retorna a URL de download da versão do Vigia

	url, _ := s.versionUrlRepositoryCache.GetVersionUrl(version)

	if url == nil {
		result, err := s.versionRepository.FindVersion(version)
		if err != nil {
			return nil, errors.New("version not found")
		}

		url, err = s.bucketService.GetVersionPreSignedUrl(result.Version)

		if err != nil {
			return nil, err
		}

		s.versionUrlRepositoryCache.SetVersionUrl(result.Version, *url)
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
