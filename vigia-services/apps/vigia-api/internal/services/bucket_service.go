package services

import (
	"context"
	"fmt"
	"time"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type BucketService struct {
	credentials *models.CloudSettings
}

func NewBucketService(cloudSettings *models.CloudSettings) *BucketService {
	return &BucketService{credentials: cloudSettings}
}

func (s *BucketService) GetVersionPreSignedUrl(version string) (*string, error) {
	cred := credentials.NewStaticCredentialsProvider(
		s.credentials.AccessKeyID,
		s.credentials.SecretAccessKey,
		s.credentials.SessionToken,
	)

	cfg, err := config.LoadDefaultConfig(
		context.Background(),
		config.WithRegion(s.credentials.Region),
		config.WithCredentialsProvider(cred),
	)

	if err != nil {
		return nil, err
	}

	s3Client := s3.NewFromConfig(cfg)
	bucketName := s.credentials.Bucket
	objectKey := fmt.Sprintf("releases/%s/%s", "fall-detection", version)
	

	presignClient := s3.NewPresignClient(s3Client)
	
	presignedUrl, err := presignClient.PresignGetObject(context.TODO(),
		&s3.GetObjectInput{
			Bucket: aws.String(bucketName),
			Key:    aws.String(objectKey),
		},
		s3.WithPresignExpires(time.Hour * 1),
	)

	if err != nil {
		return nil, err
	}
	return &presignedUrl.URL, nil
}
