package dtos

type NewVersionDTO struct {
	Version string `json:"version" binding:"required"`
}