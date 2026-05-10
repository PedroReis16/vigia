package migrations

import "embed"

// FS holds SQL migrations embedded at build time for goose.
//
//go:embed *.sql
var FS embed.FS
