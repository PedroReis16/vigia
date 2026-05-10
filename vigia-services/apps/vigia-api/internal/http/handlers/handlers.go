package handlers

type Handlers struct {
	DevicesHandler     *DevicesHandler
	HealthCheckHandler *HealthCheckHandler
	FiwareHandler      *FiwareHandler
	VersionHandler     *VersionHandler
}

func NewHandlers(
	devicesHandler *DevicesHandler, 
	healthCheckHandler *HealthCheckHandler, 
	fiwareHandler *FiwareHandler,
	versionHandler *VersionHandler) *Handlers {
	return &Handlers{
		DevicesHandler:     devicesHandler,
		HealthCheckHandler: healthCheckHandler,
		FiwareHandler:      fiwareHandler,
		VersionHandler:     versionHandler,
	}
}
