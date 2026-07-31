using Vigia.API.Contracts;
using Vigia.Database.Contracts;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;
using Vigia.Models.Extensions;
using Vigia.Fiware.Contracts;
using System.Text.RegularExpressions;
using Group = Vigia.Models.Entities.Group;
using Vigia.API.Contracts.CacheServices;
using Vigia.Models.Contracts;
using Vigia.Models.Helpers;

namespace Vigia.API.Services;

internal class DevicesService(ILogger<DevicesService> logger, IServiceScopeFactory scopeFactory) : IDevicesService
{
    private readonly ILogger<DevicesService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task<DeviceDTO?> GetDeviceAsync(Guid deviceId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            Device? device = await GetDeviceAsync(scope, deviceId);

            if (device == null)
                return null;

            return MapDeviceToDTO(device);
        }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar obter o dispositivo {deviceId}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            throw;
        }
    }

    public async Task RegisterDeviceAsync(NewDeviceDTO newDevice)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();

            if (!Regex.IsMatch(newDevice.Name, @"^Vigia-[0-9a-f]{8}$"))
                throw new EntityValidationException(nameof(newDevice.Name), "Nome do dispositivo inválido", ErrorCodes.INVALID_DEVICE_NAME);

            if (string.IsNullOrWhiteSpace(newDevice.SignPublicKey))
                throw new EntityValidationException(nameof(newDevice.SignPublicKey), "A chave pública do dispositivo é obrigatória", ErrorCodes.SIGN_PUBLIC_KEY_REQUIRED);

            if (!Validators.IsValidEd25519PublicKeyHex(newDevice.SignPublicKey))
                throw new EntityValidationException(nameof(newDevice.SignPublicKey), "A chave pública do dispositivo não é válida", ErrorCodes.INVALID_SIGN_PUBLIC_KEY);

            string normalizedSignPublicKey = newDevice.SignPublicKey.ToLowerInvariant();

            Device newDeviceEntity = new()
            {
                Id = newDevice.Id,
                Name = newDevice.Name,
                MacAddress = newDevice.MacAddress,
                SignPublicKey = normalizedSignPublicKey
            };

            Device? trackedDevice = await devicesDao.FindAsync(newDevice.Id);

            if (trackedDevice != null)
            {
                _logger.LogWarning($"O dispositivo '{newDevice.Id}' já esta registrado no sistema. Etapa de registro sendo ignorada");
                return;
            }

            IFiwareService fiwareService = scope.ServiceProvider.GetRequiredService<IFiwareService>();

            try
            {
                await fiwareService.RegisterSensorAsync(newDevice.Id, newDevice.Name);
                _logger.LogInformation($"Dispositivo {newDevice.Id} registrado no FIWARE com sucesso");
            }
            catch (Exception ex)
            {
                string errorMsg = $"Houve um erro ao tentar registrar o dispositivo no FIWARE: {ex.GetFullMessage()}";
                _logger.LogError(errorMsg);
                throw new Exception(errorMsg);
            }

            try
            {
                await devicesDao.AddAsync(newDeviceEntity);
            }
            catch (Exception ex)
            {
                // Se der erro ao salvar no banco, tenta apagar o sensor do FIWARE
                await fiwareService.DeleteSensorAsync(newDevice.Id, newDevice.Name);
                string errorMsg = $"Houve um erro ao registar o dispositivo no banco de dados: {ex.GetFullMessage()}";
                _logger.LogError(errorMsg);
                throw new Exception(errorMsg);
            }

            IDeviceSignPublicKeyProvider signPublicKeyProvider = scope.ServiceProvider.GetRequiredService<IDeviceSignPublicKeyProvider>();
            signPublicKeyProvider.SetSignPublicKey(newDevice.Id, normalizedSignPublicKey);

            _logger.LogInformation($"Dispositivo {newDevice.Id} registrado com sucesso");
        }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar registrar o dispositivo {newDevice.Id}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            throw;
        }
    }

    public async Task TrackDeviceUserAsync(Guid deviceId, Guid userId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();

            Device? device = await devicesDao.FindAsync(deviceId);

            if (device == null)
                throw new EntityValidationException(nameof(Device), "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);


            IUserDao userDao = scope.ServiceProvider.GetRequiredService<IUserDao>();
            User? deviceOwner = await userDao.FindAsync(userId);

            if (deviceOwner == null)
                throw new EntityValidationException(nameof(User), "Usuário não encontrado", ErrorCodes.USER_NOT_FOUND);

            Group userGroup = deviceOwner.LinkedGroups.First(g => g.OwnerId == userId);

            if (device.Group != null && device.Group.OwnerId != userId)
                throw new EntityValidationException(nameof(Device), "O dispositivo já esta vinculado a outro usuário", ErrorCodes.DEVICE_ALREADY_IN_USE);

            device.Group = userGroup;

            await devicesDao.UpdateDeviceGroupAsync(device);

            _logger.LogInformation($"Dispositivo {deviceId} vinculado ao usuário {userId} com sucesso");
        }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar vincular o dispositivo {deviceId} ao usuário {userId}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            throw;
        }
    }

    public async Task UntrackedDeviceUserAsync(Guid deviceId, Guid userId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            Device? device = await GetDeviceAsync(scope, deviceId);

            if (device == null)
                throw new EntityValidationException(nameof(Device), "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

            if (device.Group == null)
            {
                _logger.LogWarning($"O dispositivo {deviceId} não esta vinculado a nenhum usuário. Etapa de desvinculação sendo ignorada");
                return;
            }

            if (device.Group.OwnerId != userId)
            {
                _logger.LogWarning($"Tentativa de desvincular o dispositivo '{deviceId}' de um usuário diferente do proprietário do dispositivo ");
                throw new UnauthorizedAccessException($"Somente o proprietário do dispositivo '{deviceId}' pode remove-lo");
            }

            device.Group = null;

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();
            await devicesDao.UpdateDeviceGroupAsync(device);

            _logger.LogInformation($"Dispositivo'{deviceId}' desvinculado do usuário '{userId}' com sucesso");
        }
        catch (EntityValidationException) { throw; }
        catch (UnauthorizedAccessException) { throw; }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar desvincular o dispositivo {deviceId} do usuário {userId}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            throw;
        }
    }

    private async Task<Device?> GetDeviceAsync(IServiceScope scope, Guid deviceId)
    {
        IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();
        return await devicesDao.FindAsync(deviceId);
    }


    public async Task<List<DeviceDTO>> ListDevicesAsync(
        Guid userId,
        string? nickname = null,
        DeviceRooms? room = null,
        bool onlyShared = false,
        bool onlyOwned = false,
        int page = 1,
        int pageSize = 10)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();

            List<Device> devices = await devicesDao.GetUserDevicesAsync(
                userId,
                nickname,
                room,
                onlyShared,
                onlyOwned,
                page,
                pageSize
            );


            return devices.Select(device =>
            {
                DeviceDTO dto = MapDeviceToDTO(device);
                dto.ThumbnailUrl = GetDeviceThumbnailUrl(scope, userId, device.Id);
                return dto;
            }).ToList();
        }
        catch (EntityValidationException)
        {
            throw;
        }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar listar os dispositivos: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            throw;
        }
    }

    private string? GetDeviceThumbnailUrl(IServiceScope scope, Guid userId, Guid deviceId)
    {

        byte[]? frame = GetDeviceFrame(deviceId);
        if (frame == null)
            return null;

        IFrameAccessTokenProvider frameAccessTokenProvider =
            scope.ServiceProvider.GetRequiredService<IFrameAccessTokenProvider>();
        IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();
        string apiBasePath = configuration.GetValue<string>("BasePath")?.Trim('/') ?? string.Empty;
        string urlPrefix = string.IsNullOrEmpty(apiBasePath) ? string.Empty : $"/{apiBasePath}";

        string accessToken = frameAccessTokenProvider.IssueToken(userId, deviceId);
        return $"{urlPrefix}/devices/{deviceId}/frame?accessToken={accessToken}";
    }

    private DeviceDTO MapDeviceToDTO(Device device)
    {
        return new DeviceDTO
        {
            Id = device.Id,
            Nickname = device.Nickname ?? device.Name,
            MacAddress = device.MacAddress,
            Room = device.Room,
            OwnerId = device.Group?.OwnerId
        };
    }

    public async Task UpdateDeviceAsync(Guid userId, Guid deviceId, UpdateDeviceDTO updatedDevice)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            Device? device = await GetDeviceAsync(scope, deviceId);

            if (device == null)
                throw new EntityValidationException(nameof(Device), "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

            if (device.Group!.OwnerId != userId)
            {
                _logger.LogWarning($"Tentativa de atualizar um dispositivo '{deviceId}' de outro usuário diferente do usuário proprietário");
                throw new UnauthorizedAccessException($"Somente o proprietário do dispositivo '{deviceId}' pode atualizar suas informações");
            }

            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();

            Device updatedDeviceEntity = new()
            {
                Id = deviceId,
                Nickname = updatedDevice.Nickname ?? device.Nickname,
                Room = updatedDevice.Room ?? device.Room
            };

            if (
                !string.IsNullOrEmpty(updatedDevice.Nickname) &&
                !string.IsNullOrEmpty(device.Nickname) &&
                updatedDevice.Nickname == device.Nickname &&
                updatedDevice.Room == device.Room)
            {
                _logger.LogInformation($"A solicitação de atualização do dispositivo '{deviceId}' foi ignorada pois a solicitação não aplica mudanças efetivas sobre o dispositivo");
                return;
            }

            //TODO: Criar log com as alterações de antes e depois do dispositivo

            await devicesDao.UpdateAsync(updatedDeviceEntity);

            _logger.LogInformation($"Dispositivo '{deviceId}' atualizado com sucesso");
        }
        catch (EntityValidationException) { throw; }
        catch (UnauthorizedAccessException) { throw; }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar atualizar o dispositivo {deviceId}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            throw;
        }
    }

    public void SaveDeviceFrame(Guid deviceId, Stream frame)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDeviceFrameCacheService cacheService = scope.ServiceProvider.GetRequiredService<IDeviceFrameCacheService>();

            byte[] frameBytes = new byte[frame.Length];
            _ = frame.Read(frameBytes, 0, frameBytes.Length);

            cacheService.SetFrame(deviceId, frameBytes);

            _logger.LogInformation($"Frame do dispositivo {deviceId} salvo com sucesso");
        }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar salvar o frame do dispositivo {deviceId}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
        }
    }

    public byte[]? GetDeviceFrame(Guid deviceId)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IDeviceFrameCacheService cacheService = scope.ServiceProvider.GetRequiredService<IDeviceFrameCacheService>();

            return cacheService.GetFrame(deviceId);
        }
        catch (Exception ex)
        {
            string errorMsg = $"Houve um erro ao tentar obter o frame do dispositivo {deviceId}: {ex.GetFullMessage()}";
            _logger.LogError(errorMsg);
            return null;
        }
    }
}