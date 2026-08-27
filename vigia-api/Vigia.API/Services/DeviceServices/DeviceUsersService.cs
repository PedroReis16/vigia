using Vigia.API.Contracts.Devices;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Devices;
using Vigia.API.Models.DTOs.Users;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services.Devices;

public class DeviceUsersService(ILogger<DeviceUsersService> logger, IServiceScopeFactory scopeFactory) : IDeviceUsersService
{
    private readonly ILogger<DeviceUsersService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task<List<DeviceUserDTO>> GetDeviceUsersAsync(Guid deviceId, Guid requestingUserId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();
            Device? device = await devicesDao.FindAsync(deviceId);

            if (device == null)
                throw new EntityValidationException(nameof(Device), $"Dispositivo '{deviceId}' não encontrado para a listagem de usuários vinculados ao mesmo", ErrorCodes.DEVICE_NOT_FOUND);

            if (device.Group == null)
                throw new EntityValidationException(nameof(Device), $"Dispositivo '{deviceId}' encontrado, porém ele não está vinculado a nenhum usuário", ErrorCodes.DEVICE_GROUP_REQUIRED);

            IGroupDao groupDao = scope.ServiceProvider.GetRequiredService<IGroupDao>();
            if (!await groupDao.IsUserInGroupAsync(device.Group.Id, requestingUserId))
                throw new UnauthorizedAccessException($"Usuário sem permissão para listar os usuários do dispositivo '{deviceId}'");

            IUserService usersService = scope.ServiceProvider.GetRequiredService<IUserService>();
            List<UserDTO> users = await usersService.GetGroupUsersAsync(device.Group.Id);

            return users.Select(user => new DeviceUserDTO
            {
                Id = user.Id,
                Name = user.Name,
                UserPictureUrl = user.UserPictureUrl,
                IsOwner = device.Group.OwnerId == user.Id,
            }).ToList();
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

    public async Task RemoveDeviceUserAsync(Guid deviceId, Guid targetUserId, Guid requestingUserId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();
            Device? device = await devicesDao.FindAsync(deviceId);

            if (device == null)
                throw new EntityValidationException(nameof(Device), "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

            if (device.Group == null)
                throw new EntityValidationException(nameof(Device), "Dispositivo não está vinculado a nenhum grupo", ErrorCodes.DEVICE_GROUP_REQUIRED);

            bool isOwner = device.Group.OwnerId == requestingUserId;
            bool isSelfLeave = targetUserId == requestingUserId;

            if (!isOwner && !isSelfLeave)
                throw new UnauthorizedAccessException("Somente o proprietário pode remover outros usuários do grupo");

            if (device.Group.OwnerId == targetUserId)
                throw new EntityValidationException(nameof(Group), "O proprietário do grupo não pode ser removido", ErrorCodes.CANNOT_REMOVE_GROUP_OWNER);

            IGroupDao groupDao = scope.ServiceProvider.GetRequiredService<IGroupDao>();

            if (!isOwner && !await groupDao.IsUserInGroupAsync(device.Group.Id, requestingUserId))
                throw new UnauthorizedAccessException("Usuário sem permissão para sair deste grupo");

            Guid groupId = device.Group.Id;
            await groupDao.RemoveUserFromGroupAsync(groupId, targetUserId);

            IGroupRealtimeNotifier realtime = scope.ServiceProvider.GetRequiredService<IGroupRealtimeNotifier>();
            await realtime.NotifyMembershipRemovedAsync(groupId, targetUserId);

            _logger.LogInformation(
                "Usuário {TargetUserId} removido do grupo {GroupId} do dispositivo {DeviceId} por {RequestingUserId}",
                targetUserId, groupId, deviceId, requestingUserId);
        }
        catch (UnauthorizedAccessException) { throw; }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMessage = $"Houve um erro ao remover o usuário '{targetUserId}' do dispositivo '{deviceId}': {ex.Message}";
            _logger.LogError(ex, errorMessage);
            throw new Exception(errorMessage);
        }
    }
}
