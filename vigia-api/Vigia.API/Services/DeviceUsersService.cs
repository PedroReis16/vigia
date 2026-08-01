using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Devices;
using Vigia.API.Models.DTOs.Users;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services;

public class DeviceUsersService(ILogger<DeviceUsersService> logger, IServiceScopeFactory scopeFactory) : IDeviceUsersService
{
    private readonly ILogger<DeviceUsersService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task<List<DeviceUserDTO>> GetDeviceUsersAsync(Guid deviceId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();

            Device? device = await devicesDao.FindAsync(deviceId);

            if (device == null)
                throw new EntityValidationException(nameof(Device), $"Dispositivo '{deviceId}' não encontrado para a listagem de usuários vinculados ao mesmo", ErrorCodes.DEVICE_NOT_FOUND);

            if (device.Group == null)
                throw new EntityValidationException(nameof(Device), $"Dispositio '{deviceId}' encontrado, porém ele não está vinculado a nenhum usuário", ErrorCodes.DEVICE_GROUP_REQUIRED);

            IUserService usersService = scope.ServiceProvider.GetRequiredService<IUserService>();

            List<UserDTO> users = await usersService.GetGroupUsersAsync(device.Group.Id);

            List<DeviceUserDTO> deviceUsers = users.Select(user => new DeviceUserDTO
            {
                Id = user.Id,
                Name = user.Name,
                UserPictureUrl = user.UserPictureUrl,
                IsOwner = device.Group.OwnerId == user.Id,
            }).ToList();

            return deviceUsers;
        }
        catch (UnauthorizedAccessException) { throw; }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMessage = $"Houve um erro ao realizar a busca de usuários vinculados ao dispositivo '{deviceId}': {ex.Message}";
            _logger.LogError(errorMessage);
            throw new Exception(errorMessage);
        }
    }

}