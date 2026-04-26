module github.com/PedroReis16/vigia/vigia-services/pkg/logger

go 1.26.1

require (
	github.com/PedroReis16/vigia/vigia-services/pkg/utils v0.0.0
	go.uber.org/zap v1.27.1
	gopkg.in/natefinch/lumberjack.v2 v2.2.1
)

require (
	github.com/stretchr/testify v1.11.1 // indirect
	go.uber.org/multierr v1.10.0 // indirect
)

replace github.com/PedroReis16/vigia/vigia-services/pkg/utils => ../utils
