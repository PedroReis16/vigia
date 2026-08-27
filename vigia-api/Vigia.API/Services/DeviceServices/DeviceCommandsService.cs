using Vigia.API.Contracts.Devices;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Database.Contracts;
using Vigia.Fiware.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;
using Microsoft.AspNetCore.Http;

namespace Vigia.API.Services.Devices;

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

            bool result = await fiwareService.SendCommandAsync(
                deviceName: device.Name,
                command: deviceCommand.Command,
                commandValue: deviceCommand.CommandValue);

            if (!result)
            {
                throw new HttpResponseException(
                    StatusCodes.Status502BadGateway,
                    $"Falha ao enviar comando '{deviceCommand.Command}' para o dispositivo '{device.Name}' via FIWARE. Verifique se o device está provisionado no Orion/IoT Agent.",
                    ErrorCodes.FIWARE_COMMAND_FAILED);
            }

            return true;
        }
        catch (UnauthorizedAccessException)
        {
            throw;
        }
        catch (HttpResponseException)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending command to device {DeviceId}", deviceId);
            throw;
        }
    }

    public async Task<bool> SendUndemandStopStreamingAsync(Guid deviceId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();
            Device? device = await devicesDao.FindAsync(deviceId);

            if (device is null)
                throw new EntityValidationException(nameof(Device), "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

            IFiwareService fiwareService = scope.ServiceProvider.GetRequiredService<IFiwareService>();

            bool result = await fiwareService.SendCommandAsync(
                deviceName: device.Name,
                command: DeviceCommands.STOP_STREAMING,
                commandValue: null);

            if (!result)
            {
                throw new HttpResponseException(
                    StatusCodes.Status502BadGateway,
                    $"Falha ao enviar STOP_STREAMING para o dispositivo '{device.Name}' via FIWARE.",
                    ErrorCodes.FIWARE_COMMAND_FAILED);
            }

            return true;
        }
        catch (Exception ex) when (ex is not EntityValidationException and not HttpResponseException)
        {
            _logger.LogError(ex, "Error sending undemand STOP_STREAMING to device {DeviceId}", deviceId);
            throw;
        }
    }
}