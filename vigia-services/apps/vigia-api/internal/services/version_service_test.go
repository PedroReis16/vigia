package services

import (
	"bytes"
	"context"
	"errors"
	"io"
	"testing"

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

	findLatest    *entities.Version
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

type fakeBucket struct {
	presignURL *string
	presignErr error

	uploadErr    error
	uploadCalled bool
}

func (f *fakeBucket) GetVersionPreSignedUrl(version string) (*string, error) {
	return f.presignURL, f.presignErr
}

func (f *fakeBucket) UploadVersion(_ context.Context, _ string, _ io.Reader, _ int64) error {
	f.uploadCalled = true
	return f.uploadErr
}

func TestVersionService_GetVigiaVersion_cacheHit(t *testing.T) {
	u := "https://example.com/pkg.zip"
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{getURL: &u},
		versionRepository:         &fakeVersionStore{},
		bucketService:             &fakeBucket{},
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
	bucket := &fakeBucket{presignURL: &pre}

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
		bucketService:             &fakeBucket{},
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
		bucketService:             &fakeBucket{presignErr: errors.New("s3 down")},
	}

	_, err := svc.GetVigiaVersion("1.0.0")
	if err == nil || err.Error() != "s3 down" {
		t.Fatalf("want presign error, got %v", err)
	}
}

func TestVersionService_RegisterNewVigiaVersion(t *testing.T) {
	bucket := &fakeBucket{}
	repo := &fakeVersionStore{}
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         repo,
		bucketService:             bucket,
	}

	err := svc.RegisterNewVigiaVersion(context.Background(), "9.9.9", bytes.NewReader([]byte("data")), 4)
	if err != nil {
		t.Fatalf("RegisterNewVigiaVersion: %v", err)
	}
	if !bucket.uploadCalled {
		t.Fatal("expected UploadVersion to be called")
	}
}

func TestVersionService_RegisterNewVigiaVersion_uploadError(t *testing.T) {
	bucket := &fakeBucket{uploadErr: errors.New("s3 fail")}
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         &fakeVersionStore{},
		bucketService:             bucket,
	}

	err := svc.RegisterNewVigiaVersion(context.Background(), "1.0.0", bytes.NewReader([]byte{}), 0)
	if err == nil {
		t.Fatal("expected upload error")
	}
}

func TestVersionService_RegisterNewVigiaVersion_repoError(t *testing.T) {
	bucket := &fakeBucket{}
	repo := &fakeVersionStore{regErr: errors.New("db")}
	svc := &VersionService{
		versionUrlRepositoryCache: &fakeVersionURLCache{},
		versionRepository:         repo,
		bucketService:             bucket,
	}

	err := svc.RegisterNewVigiaVersion(context.Background(), "1.0.0", bytes.NewReader([]byte("data")), 4)
	if err == nil || err.Error() != "db" {
		t.Fatalf("want db error, got %v", err)
	}
}

func TestVersionService_FindForUpdates_noCurrent_returnsLatest(t *testing.T) {
	u := "https://example.com/latest.zip"
	v := (&entities.Version{}).NewVersion()
	v.Version = "3.0.0"
	v.IsLatest = true

	cache := &fakeVersionURLCache{}
	repo := &fakeVersionStore{findLatest: v, findVer: v}
	bucket := &fakeBucket{presignURL: &u}

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
		bucketService:             &fakeBucket{},
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
	bucket := &fakeBucket{presignURL: &u}

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
		bucketService:             &fakeBucket{},
	}

	_, err := svc.FindForUpdates("")
	if err == nil || err.Error() != "nenhuma versão disponível" {
		t.Fatalf("unexpected err: %v", err)
	}
}
