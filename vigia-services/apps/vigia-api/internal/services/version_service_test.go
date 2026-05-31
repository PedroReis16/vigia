package services

import (
	"errors"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/dtos"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/entities"
	"gorm.io/gorm"
)

type fakeVersionURLCache struct {
	getURL *string
	getErr error

	setVersion string
	setURL     string
	setCalls   int
}

func (f *fakeVersionURLCache) GetVersionUrl(version string) (*string, error) {
	return f.getURL, f.getErr
}

func (f *fakeVersionURLCache) SetVersionUrl(version string, url string) error {
	f.setVersion = version
	f.setURL = url
	f.setCalls++
	return nil
}

type fakeVersionStore struct {
	findVer *entities.Version
	findErr error

	findLatest *entities.Version
	findLatestErr error

	regErr error
}

func (f *fakeVersionStore) FindVersion(version string) (*entities.Version, error) {
	if f.findErr != nil {
		return nil, f.findErr
	}
	return f.findVer, nil
}

func (f *fakeVersionStore) FindLatestVersion() (*entities.Version, error) {
	if f.findLatestErr != nil {
		return nil, f.findLatestErr
	}
	return f.findLatest, nil
}

func (f *fakeVersionStore) RegisterVersion(newVersion *entities.Version) error {
	return f.regErr
}

type fakePresigner struct {
	url *string
	err error
}

func (f *fakePresigner) GetVersionPreSignedUrl(version string) (*string, error) {
	return f.url, f.err
}

func TestVersionService_GetVigiaVersion_cacheHit(t *testing.T) {
	u := "https://example.com/pkg.zip"
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{getURL: &u},
		versionRepository:         &fakeVersionStore{},
		bucketService:             &fakePresigner{},
	}

	out, err := svc.GetVigiaVersion("1.2.3")
	if err != nil {
		t.Fatalf("GetVigiaVersion: %v", err)
	}
	if out.Version != "1.2.3" || out.DownloadURL != u {
		t.Fatalf("unexpected dto: %+v", out)
	}
}

func TestVersionService_GetVigiaVersion_cacheMiss_presignsAndCaches(t *testing.T) {
	pre := "https://bucket/presigned"
	v := (&entities.Version{}).NewVersion()
	v.Version = "2.0.0"

	cache := &fakeVersionURLCache{}
	repo := &fakeVersionStore{findVer: v}
	bucket := &fakePresigner{url: &pre}

	svc := &VersionService{
		versionUrlRepositoryCache: cache,
		versionRepository:         repo,
		bucketService:             bucket,
	}

	out, err := svc.GetVigiaVersion("2.0.0")
	if err != nil {
		t.Fatalf("GetVigiaVersion: %v", err)
	}
	if out.Version != "2.0.0" || out.DownloadURL != pre {
		t.Fatalf("unexpected dto: %+v", out)
	}
	if cache.setCalls != 1 || cache.setVersion != "2.0.0" || cache.setURL != pre {
		t.Fatalf("cache not updated as expected: calls=%d version=%q url=%q", cache.setCalls, cache.setVersion, cache.setURL)
	}
}

func TestVersionService_GetVigiaVersion_repoNotFound(t *testing.T) {
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         &fakeVersionStore{findErr: errors.New("no row")},
		bucketService:             &fakePresigner{},
	}

	_, err := svc.GetVigiaVersion("x")
	if err == nil || err.Error() != "version not found" {
		t.Fatalf("want version not found, got %v", err)
	}
}

func TestVersionService_GetVigiaVersion_presignError(t *testing.T) {
	v := (&entities.Version{}).NewVersion()
	v.Version = "1.0.0"

	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         &fakeVersionStore{findVer: v},
		bucketService:             &fakePresigner{err: errors.New("s3 down")},
	}

	_, err := svc.GetVigiaVersion("1.0.0")
	if err == nil || err.Error() != "s3 down" {
		t.Fatalf("want presign error, got %v", err)
	}
}

func TestVersionService_RegisterNewVigiaVersion(t *testing.T) {
	repo := &fakeVersionStore{}
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         repo,
		bucketService:             &fakePresigner{},
	}

	err := svc.RegisterNewVigiaVersion(&dtos.NewVersionDTO{Version: "9.9.9"})
	if err != nil {
		t.Fatalf("RegisterNewVigiaVersion: %v", err)
	}
}

func TestVersionService_FindForUpdates_noCurrent_returnsLatest(t *testing.T) {
	u := "https://example.com/latest.zip"
	v := (&entities.Version{}).NewVersion()
	v.Version = "3.0.0"
	v.IsLatest = true

	cache := &fakeVersionURLCache{}
	repo := &fakeVersionStore{findLatest: v, findVer: v}
	bucket := &fakePresigner{url: &u}

	svc := &VersionService{
		versionUrlRepositoryCache: cache,
		versionRepository:         repo,
		bucketService:             bucket,
	}

	out, err := svc.FindForUpdates("")
	if err != nil {
		t.Fatalf("FindForUpdates: %v", err)
	}
	if out.Version != "3.0.0" || out.DownloadURL != u {
		t.Fatalf("unexpected: %+v", out)
	}
}

func TestVersionService_FindForUpdates_alreadyLatest_returnsNil(t *testing.T) {
	v := (&entities.Version{}).NewVersion()
	v.Version = "2.0.0"
	v.IsLatest = true

	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         &fakeVersionStore{findLatest: v},
		bucketService:             &fakePresigner{},
	}

	out, err := svc.FindForUpdates("2.0.0")
	if err != nil || out != nil {
		t.Fatalf("want nil,nil got %+v, %v", out, err)
	}
}

func TestVersionService_FindForUpdates_newerAvailable_returnsLatest(t *testing.T) {
	u := "https://example.com/latest.zip"
	v := (&entities.Version{}).NewVersion()
	v.Version = "2.0.0"
	v.IsLatest = true

	cache := &fakeVersionURLCache{}
	repo := &fakeVersionStore{findLatest: v, findVer: v}
	bucket := &fakePresigner{url: &u}

	svc := &VersionService{
		versionUrlRepositoryCache: cache,
		versionRepository:         repo,
		bucketService:             bucket,
	}

	out, err := svc.FindForUpdates("1.0.0")
	if err != nil {
		t.Fatalf("FindForUpdates: %v", err)
	}
	if out.Version != "2.0.0" || out.DownloadURL != u {
		t.Fatalf("unexpected: %+v", out)
	}
}

func TestVersionService_FindForUpdates_noVersionsRegistered(t *testing.T) {
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         &fakeVersionStore{findLatestErr: gorm.ErrRecordNotFound},
		bucketService:             &fakePresigner{},
	}

	_, err := svc.FindForUpdates("")
	if err == nil || err.Error() != "nenhuma versão disponível" {
		t.Fatalf("unexpected err: %v", err)
	}
}

func TestVersionService_RegisterNewVigiaVersion_repoError(t *testing.T) {
	repo := &fakeVersionStore{regErr: errors.New("db")}
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         repo,
		bucketService:             &fakePresigner{},
	}

	err := svc.RegisterNewVigiaVersion(&dtos.NewVersionDTO{Version: "1"})
	if err == nil || err.Error() != "db" {
		t.Fatalf("want db error, got %v", err)
	}
}
