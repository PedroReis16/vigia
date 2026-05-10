package config

import (
	"context"
	"database/sql"
	"log"
	"os"

	appmigrations "github.com/PedroReis16/vigia/vigia-services/apps/vigia-api/migrations"
	"github.com/pressly/goose/v3"
	"go.uber.org/fx"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func InitDatabase(lc fx.Lifecycle) *gorm.DB {
	connectionString := os.Getenv("DATABASE_CONNECTION")

	if connectionString == "" {
		log.Fatalf("DATABASE_CONNECTION is not set")
	}

	db, err := gorm.Open(postgres.Open(connectionString), &gorm.Config{})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	sqlDB, err := db.DB()
	if err != nil {
		log.Fatalf("Failed to get sql.DB from gorm: %v", err)
	}
	if err := runGooseMigrations(sqlDB); err != nil {
		log.Fatalf("Database migrations failed: %v", err)
	}

	lc.Append(fx.Hook{
		OnStart: func(ctx context.Context) error {
			return nil
		},
		OnStop: func(ctx context.Context) error {
			return sqlDB.Close()
		},
	})

	return db
}

func runGooseMigrations(sqlDB *sql.DB) error {
	goose.SetBaseFS(appmigrations.FS)
	defer goose.SetBaseFS(nil)
	if err := goose.SetDialect("postgres"); err != nil {
		return err
	}
	return goose.Up(sqlDB, ".")
}