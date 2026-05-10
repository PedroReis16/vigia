package repositories_test

import (
	"fmt"
	"sync/atomic"
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/entities"
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/repositories"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

// Unique in-memory DB per call — a fixed "file::memory:?cache=shared" DSN is shared across all tests in the process.
var sqliteMemSeq uint64

func openTestDB(t *testing.T) *gorm.DB {
	t.Helper()
	id := atomic.AddUint64(&sqliteMemSeq, 1)
	db, err := gorm.Open(sqlite.Open(fmt.Sprintf("file:memdb_%d?mode=memory&cache=shared", id)), &gorm.Config{})
	if err != nil {
		t.Fatalf("open db: %v", err)
	}
	// Schema aligned with entities.Version but SQLite-friendly (AutoMigrate uses Postgres-oriented defaults from tags).
	if err := db.Exec(`
CREATE TABLE IF NOT EXISTS versions (
	id TEXT PRIMARY KEY,
	created_at DATETIME,
	updated_at DATETIME,
	deleted_at DATETIME,
	version VARCHAR(20) NOT NULL UNIQUE,
	is_latest INTEGER NOT NULL DEFAULT 1
);`).Error; err != nil {
		t.Fatalf("schema: %v", err)
	}
	return db
}

func TestVersionRepository_FindVersion(t *testing.T) {
	db := openTestDB(t)
	repo := repositories.NewVersionRepository(db)

	v := (&entities.Version{}).NewVersion()
	v.Version = "1.0.0"
	if err := db.Create(v).Error; err != nil {
		t.Fatal(err)
	}

	got, err := repo.FindVersion("1.0.0")
	if err != nil {
		t.Fatal(err)
	}
	if got.Version != "1.0.0" {
		t.Fatalf("got %q", got.Version)
	}
}

func TestVersionRepository_RegisterVersion_setsLatest(t *testing.T) {
	db := openTestDB(t)
	repo := repositories.NewVersionRepository(db)

	a := (&entities.Version{}).NewVersion()
	a.Version = "1.0.0"
	if err := repo.RegisterVersion(a); err != nil {
		t.Fatal(err)
	}

	b := (&entities.Version{}).NewVersion()
	b.Version = "2.0.0"
	if err := repo.RegisterVersion(b); err != nil {
		t.Fatal(err)
	}

	var old entities.Version
	if err := db.Where("version = ?", "1.0.0").First(&old).Error; err != nil {
		t.Fatal(err)
	}
	if old.IsLatest {
		t.Fatal("1.0.0 should not be latest")
	}

	var latest entities.Version
	if err := db.Where("version = ?", "2.0.0").First(&latest).Error; err != nil {
		t.Fatal(err)
	}
	if !latest.IsLatest {
		t.Fatal("2.0.0 should be latest")
	}
}

func TestVersionRepository_FindLatestVersion(t *testing.T) {
	db := openTestDB(t)
	repo := repositories.NewVersionRepository(db)

	a := (&entities.Version{}).NewVersion()
	a.Version = "1.0.0"
	if err := repo.RegisterVersion(a); err != nil {
		t.Fatal(err)
	}
	b := (&entities.Version{}).NewVersion()
	b.Version = "2.0.0"
	if err := repo.RegisterVersion(b); err != nil {
		t.Fatal(err)
	}

	got, err := repo.FindLatestVersion()
	if err != nil {
		t.Fatal(err)
	}
	if got.Version != "2.0.0" || !got.IsLatest {
		t.Fatalf("unexpected latest: %+v", got)
	}
}

func TestVersionRepository_RegisterVersion_sameVersionNoOp(t *testing.T) {
	db := openTestDB(t)
	repo := repositories.NewVersionRepository(db)

	a := (&entities.Version{}).NewVersion()
	a.Version = "1.0.0"
	if err := repo.RegisterVersion(a); err != nil {
		t.Fatal(err)
	}

	dup := (&entities.Version{}).NewVersion()
	dup.Version = "1.0.0"
	if err := repo.RegisterVersion(dup); err != nil {
		t.Fatal(err)
	}

	var count int64
	if err := db.Model(&entities.Version{}).Count(&count).Error; err != nil {
		t.Fatal(err)
	}
	if count != 1 {
		t.Fatalf("want 1 row, got %d", count)
	}
}
