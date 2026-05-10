package cache

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

type VersionUrlRepositoryCache struct {
	cache *redis.Client
}

func NewVersionUrlRepositoryCache(cache *redis.Client) *VersionUrlRepositoryCache {
	return &VersionUrlRepositoryCache{cache: cache}
}

const VERSION_URL_KEY = "version:url:"

func (r *VersionUrlRepositoryCache) GetVersionUrl(version string) (*string, error) {
	if version == "" {
		return nil, fmt.Errorf("version cannot be empty")
	}
	url, err := r.cache.Get(context.Background(), VERSION_URL_KEY+version).Result()
	if err == redis.Nil {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &url, nil
}

func (r *VersionUrlRepositoryCache) SetVersionUrl(version string, url string) error {
	return r.cache.Set(context.Background(), VERSION_URL_KEY+version, url, 1*time.Hour).Err()
}

func (r *VersionUrlRepositoryCache) DeleteVersionUrl(version string) error {
	return r.cache.Del(context.Background(), VERSION_URL_KEY+version).Err()
}
