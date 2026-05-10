package handlers

type Handlers struct {
	DevicesHandler *DevicesHandler
	HealthCheckHandler *HealthCheckHandler
	FiwareHandler *FiwareHandler
}

func NewHandlers(devicesHandler *DevicesHandler, healthCheckHandler *HealthCheckHandler, fiwareHandler *FiwareHandler) *Handlers {
	return &Handlers{
		DevicesHandler: devicesHandler,
		HealthCheckHandler: healthCheckHandler,
		FiwareHandler: fiwareHandler,
	}
}