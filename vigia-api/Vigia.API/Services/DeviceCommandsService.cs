using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Database.Contracts;
using Vigia.Fiware.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services;

internal class DeviceCommandsService(ILogger<DeviceCommandsService> logger, IServiceScopeFactory scopeFactory) : IDeviceCommandsService
{
    private readonly ILogger<DeviceCommandsService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task<bool> SendCommandAsync(Guid deviceId, Guid userId, DeviceCommandDTO deviceCommand)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();


            Task<Device?> getDeviceTask = devicesDao.FindAsync(deviceId);
            Task<List<Device>> getUserDevicesTask = devicesDao.GetUserDevicesAsync(userId);

            await Task.WhenAll(getDeviceTask, getUserDevicesTask);

            Device? device = getDeviceTask.Result;

            List<Device> userDevices = getUserDevicesTask.Result;

            if (device is null || device.Group is null)
                throw new EntityValidationException(nameof(Device), "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

            if (!userDevices.Any(d => d.Id == deviceId))
            {
                _logger.LogWarning($"O usuário '{userId}' tentou enviar um comando para o dispositivo '{deviceId}', no qual ele não está na lista de usuários com acesso a este dispositivo");
                throw new UnauthorizedAccessException($"Você não tem permissão para enviar comandos para o dispositivo '{deviceId}'");
            }

            if (deviceCommand.Command != DeviceCommands.START_STREAMING && deviceCommand.Command != DeviceCommands.STOP_STREAMING && device.Group.OwnerId != userId)
            {
                _logger.LogWarning($"O usuário '{userId}' tentou enviar um comando para o dispositivo '{deviceId}', no qual ele não é o proprietário do dispositivo");
                throw new UnauthorizedAccessException("Somente o proprietário do dispositivo pode prosseguir com esse comando");
            }

            IFiwareService fiwareService = scope.ServiceProvider.GetRequiredService<IFiwareService>();

            var result = await fiwareService.SendCommandAsync(deviceName: device.Name, command: deviceCommand.Command, commandValue: deviceCommand.CommandValue);

            return result;
        }
        catch (UnauthorizedAccessException)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending command to device {DeviceId}", deviceId);
            throw;
        }
    }
}