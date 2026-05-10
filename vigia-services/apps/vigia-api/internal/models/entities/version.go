package entities

import (
)

type Version struct {
	*BaseEntity
	Version string `gorm:"type:varchar(20);index;not null;unique"`
	IsLatest bool `gorm:"type:boolean;default:true;index;"`
}	

func (entity *Version) NewVersion() *Version {
	base := (&BaseEntity{}).NewBaseEntity()
	return &Version{
		BaseEntity: &base,
		Version:    "1.0.0",
		IsLatest:   true,
	}
}