package models

type CloudSettings struct {
	Bucket          string
	Region          string
	AccessKeyID     string
	SecretAccessKey string
	SessionToken    string
	Endpoint        string
	UsePathStyle    bool
}
