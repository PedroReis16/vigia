package repositories

import (
	"github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/internal/models/entities"
	"gorm.io/gorm"
)

type VersionRepository struct {
	db *gorm.DB
}

func NewVersionRepository(db *gorm.DB) *VersionRepository {
	return &VersionRepository{db: db}
}

func (r *VersionRepository) FindVersion(version string) (*entities.Version, error) {
	var result entities.Version
	err := r.db.Where("version = ?", version).First(&result).Error
	if err != nil {
		return nil, err
	}
	return &result, nil
}

func (r *VersionRepository) RegisterVersion(newVersion *entities.Version) error {

	var oldVersion entities.Version
	// Busca a versão marcada como is_latest
	err := r.db.Where("is_latest = true").First(&oldVersion).Error
	if err != nil && err != gorm.ErrRecordNotFound {
		return err
	}

	// Se já existe uma versão marcada como latest e for igual ao que estamos tentando inserir, retorna erro
	if err == nil && oldVersion.Version == newVersion.Version {
		return nil // Ou pode retornar um erro: fmt.Errorf("versão já está marcada como latest")
	}

	// Remove a flag is_latest da versão anterior (se existir)
	if err == nil {
		oldVersion.IsLatest = false
		if err := r.db.Save(&oldVersion).Error; err != nil {
			return err
		}
	}

	// Marca a nova versão como latest
	newVersion.IsLatest = true
	if err := r.db.Create(&newVersion).Error; err != nil {
		return err
	}

	return nil
}

func (r *VersionRepository) FindNewerVersion(version string) (*entities.Version, error) {

	return nil, nil
}
