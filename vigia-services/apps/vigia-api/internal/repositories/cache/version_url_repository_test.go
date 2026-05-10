package cache_test

import (
	"testing"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/repositories/cache"
	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

func TestVersionUrlRepositoryCache_GetVersionUrl_emptyVersion(t *testing.T) {
	s := miniredis.RunT(t)
	rdb := redis.NewClient(&redis.Options{Addr: s.Addr()})
	repo := cache.NewVersionUrlRepositoryCache(rdb)

	_, err := repo.GetVersionUrl("")
	if err == nil {
		t.Fatal("expected error for empty version")
	}
}

func TestVersionUrlRepositoryCache_GetSetRoundTrip(t *testing.T) {
	s := miniredis.RunT(t)
	rdb := redis.NewClient(&redis.Options{Addr: s.Addr()})
	repo := cache.NewVersionUrlRepositoryCache(rdb)

	u, err := repo.GetVersionUrl("1.0.0")
	if err != nil {
		t.Fatal(err)
	}
	if u != nil {
		t.Fatalf("expected cache miss, got %v", *u)
	}

	const want = "https://cdn.example.com/a.zip"
	if err := repo.SetVersionUrl("1.0.0", want); err != nil {
		t.Fatal(err)
	}

	got, err := repo.GetVersionUrl("1.0.0")
	if err != nil {
		t.Fatal(err)
	}
	if got == nil || *got != want {
		t.Fatalf("got %v want %q", got, want)
	}
}

func TestVersionUrlRepositoryCache_DeleteVersionUrl(t *testing.T) {
	s := miniredis.RunT(t)
	rdb := redis.NewClient(&redis.Options{Addr: s.Addr()})
	repo := cache.NewVersionUrlRepositoryCache(rdb)

	if err := repo.SetVersionUrl("v", "url"); err != nil {
		t.Fatal(err)
	}
	if err := repo.DeleteVersionUrl("v"); err != nil {
		t.Fatal(err)
	}
	got, err := repo.GetVersionUrl("v")
	if err != nil {
		t.Fatal(err)
	}
	if got != nil {
		t.Fatalf("expected deleted, got %v", *got)
	}
}
