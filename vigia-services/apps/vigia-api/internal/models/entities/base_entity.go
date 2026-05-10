package entities

import (
	"time"

	"github.com/google/uuid"
)

type BaseEntity struct {
	Id        uuid.UUID `gorm:"type:uuid;primary_key;index"`
	CreatedAt time.Time `gorm:"type:timestamp;index;default:now()"`
	UpdatedAt time.Time `gorm:"type:timestamp;index;default:null"`
	DeletedAt time.Time `gorm:"type:timestamp;index;default:null"`
}

func (entity *BaseEntity) NewBaseEntity() BaseEntity {
	return BaseEntity{
		Id:        uuid.New(),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		DeletedAt: time.Time{},
	}
}