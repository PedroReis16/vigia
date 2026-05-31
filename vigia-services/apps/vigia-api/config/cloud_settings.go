package config

import (
	"os"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models"
)

func GetAwsSettings() *models.CloudSettings {
	return &models.CloudSettings{
		Bucket:          os.Getenv("S3_VIGIA_BUCKET"),
		Region:          os.Getenv("S3_VIGIA_REGION"),
		AccessKeyID:     os.Getenv("S3_VIGIA_ACCESS_KEY_ID"),
		SecretAccessKey: os.Getenv("S3_VIGIA_SECRET_ACCESS_KEY"),
		SessionToken:    os.Getenv("S3_VIGIA_SESSION_TOKEN"),
		Endpoint:        os.Getenv("S3_VIGIA_ENDPOINT"),
		UsePathStyle:    os.Getenv("S3_VIGIA_PATH_STYLE") == "true",
	}
}
