package services

import (
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"
)


type DeviceService struct{
	cacheService *redis.Client
	logger *zap.Logger
}

func NewDeviceService() *DeviceService{
	return &DeviceService{}
}
