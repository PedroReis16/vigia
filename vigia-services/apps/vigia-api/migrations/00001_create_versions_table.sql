-- +goose Up
-- +goose StatementBegin
CREATE TABLE versions (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    version VARCHAR(20) NOT NULL,
    is_latest BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uix_versions_version UNIQUE (version)
);

CREATE INDEX idx_versions_created_at ON versions (created_at);
CREATE INDEX idx_versions_deleted_at ON versions (deleted_at);
CREATE INDEX idx_versions_is_latest ON versions (is_latest);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS versions;
-- +goose StatementEnd
