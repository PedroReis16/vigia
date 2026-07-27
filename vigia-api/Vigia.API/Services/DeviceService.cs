using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Models.Extensions;

namespace Vigia.API.Services;

internal class DeviceService(ILogger<IDeviceService> logger, IServiceScopeFactory scopeFactory) : IDeviceService
{
    private readonly ILogger<IDeviceService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task RegisterDeviceAsync(NewDeviceDTO newDevice)
    {
        try
        {

        }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar registrar o dispositivo {newDevice.Id}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            throw;
        }
    }
}