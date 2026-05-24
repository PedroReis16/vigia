package services

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

const releaseObjectKey = "releases/fall-detection/%s/vigia-fall-detection-linux-arm64.tar.gz"

type BucketService struct {
	credentials *models.CloudSettings
}

func NewBucketService(cloudSettings *models.CloudSettings) *BucketService {
	return &BucketService{credentials: cloudSettings}
}

func (s *BucketService) newS3Client(ctx context.Context) (*s3.Client, error) {
	cred := credentials.NewStaticCredentialsProvider(
		s.credentials.AccessKeyID,
		s.credentials.SecretAccessKey,
		s.credentials.SessionToken,
	)
	cfg, err := config.LoadDefaultConfig(
		ctx,
		config.WithRegion(s.credentials.Region),
		config.WithCredentialsProvider(cred),
	)
	if err != nil {
		return nil, err
	}
	return s3.NewFromConfig(cfg, func(o *s3.Options) {
		if s.credentials.Endpoint != "" {
			o.BaseEndpoint = aws.String(s.credentials.Endpoint)
		}
		o.UsePathStyle = s.credentials.UsePathStyle
	}), nil
}

func (s *BucketService) GetVersionPreSignedUrl(version string) (*string, error) {
	client, err := s.newS3Client(context.Background())
	if err != nil {
		return nil, err
	}

	presignClient := s3.NewPresignClient(client)
	presignedUrl, err := presignClient.PresignGetObject(context.TODO(),
		&s3.GetObjectInput{
			Bucket: aws.String(s.credentials.Bucket),
			Key:    aws.String(fmt.Sprintf(releaseObjectKey, version)),
		},
		s3.WithPresignExpires(time.Hour),
	)
	if err != nil {
		return nil, err
	}
	return &presignedUrl.URL, nil
}

func (s *BucketService) UploadVersion(ctx context.Context, version string, reader io.Reader, size int64) error {
	client, err := s.newS3Client(ctx)
	if err != nil {
		return err
	}

	_, err = client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:        aws.String(s.credentials.Bucket),
		Key:           aws.String(fmt.Sprintf(releaseObjectKey, version)),
		Body:          reader,
		ContentLength: aws.Int64(size),
		ContentType:   aws.String("application/gzip"),
	})
	return err
}
