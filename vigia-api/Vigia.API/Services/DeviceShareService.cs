using System.Security.Cryptography;
using Microsoft.Extensions.Configuration;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services;

public class DeviceShareService(
    ILogger<DeviceShareService> logger,
    IServiceScopeFactory scopeFactory,
    IConfiguration configuration,
    IHttpContextAccessor httpContextAccessor) : IDeviceShareService
{
    public const int MaxGroupUsers = 10;
    private static readonly TimeSpan InviteLifetime = TimeSpan.FromDays(7);

    private readonly ILogger<DeviceShareService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;
    private readonly IConfiguration _configuration = configuration;
    private readonly IHttpContextAccessor _httpContextAccessor = httpContextAccessor;

    public async Task<DeviceShareInviteDTO> GenerateInviteAsync(Guid deviceId, Guid userId)
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

            if (device.Group.OwnerId != userId)
                throw new UnauthorizedAccessException("Somente o proprietário do dispositivo pode gerar links de compartilhamento");

            IGroupDao groupDao = scope.ServiceProvider.GetRequiredService<IGroupDao>();
            int memberCount = await groupDao.CountMembersAsync(device.Group.Id);

            if (memberCount >= MaxGroupUsers)
                throw new EntityValidationException(nameof(Group), "O grupo já atingiu o limite de 10 usuários", ErrorCodes.GROUP_USER_LIMIT_REACHED);

            IGroupInviteDao inviteDao = scope.ServiceProvider.GetRequiredService<IGroupInviteDao>();
            await inviteDao.RevokeActiveInvitesForGroupAsync(device.Group.Id);

            // Short opaque code (not a session/JWT). ~72 bits of entropy.
            string code = CreateInviteCode();
            DateTime expiresAt = DateTime.UtcNow.Add(InviteLifetime);

            GroupInvite invite = new()
            {
                Token = code,
                GroupId = device.Group.Id,
                CreatedByUserId = userId,
                ExpiresAt = expiresAt,
            };

            await inviteDao.AddAsync(invite);

            string publicShareBase = ResolvePublicShareBase();

            _logger.LogInformation("Convite gerado para o grupo {GroupId} do dispositivo {DeviceId}", device.Group.Id, deviceId);

            return new DeviceShareInviteDTO
            {
                Token = code,
                InviteUrl = $"{publicShareBase}{code}",
                ExpiresAt = expiresAt,
            };
        }
        catch (UnauthorizedAccessException) { throw; }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMessage = $"Houve um erro ao gerar o link de compartilhamento do dispositivo '{deviceId}': {ex.Message}";
            _logger.LogError(ex, errorMessage);
            throw new Exception(errorMessage);
        }
    }

    public async Task AcceptInviteAsync(string token, Guid userId)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(token))
                throw new EntityValidationException(nameof(token), "O token do convite é obrigatório", ErrorCodes.TOKEN_REQUIRED);

            using IServiceScope scope = _scopeFactory.CreateScope();

            IGroupInviteDao inviteDao = scope.ServiceProvider.GetRequiredService<IGroupInviteDao>();
            GroupInvite? invite = await inviteDao.FindByTokenAsync(token, track: true);

            if (invite == null || invite.RevokedAt != null)
                throw new EntityValidationException(nameof(token), "Convite inválido ou revogado", ErrorCodes.INVITE_INVALID);

            if (invite.ExpiresAt <= DateTime.UtcNow)
                throw new EntityValidationException(nameof(token), "Convite expirado", ErrorCodes.INVITE_EXPIRED);

            IGroupDao groupDao = scope.ServiceProvider.GetRequiredService<IGroupDao>();

            if (await groupDao.IsUserInGroupAsync(invite.GroupId, userId))
            {
                _logger.LogInformation("Usuário {UserId} já é membro do grupo {GroupId}", userId, invite.GroupId);
                return;
            }

            int memberCount = await groupDao.CountMembersAsync(invite.GroupId);
            if (memberCount >= MaxGroupUsers)
                throw new EntityValidationException(nameof(Group), "O grupo já atingiu o limite de 10 usuários", ErrorCodes.GROUP_USER_LIMIT_REACHED);

            await groupDao.AddUserToGroupAsync(invite.GroupId, userId);

            IGroupRealtimeNotifier realtime = scope.ServiceProvider.GetRequiredService<IGroupRealtimeNotifier>();
            await realtime.NotifyMembershipJoinedAsync(invite.GroupId, userId);

            _logger.LogInformation("Usuário {UserId} aceitou convite e entrou no grupo {GroupId}", userId, invite.GroupId);
        }
        catch (UnauthorizedAccessException) { throw; }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMessage = $"Houve um erro ao aceitar o convite de compartilhamento: {ex.Message}";
            _logger.LogError(ex, errorMessage);
            throw new Exception(errorMessage);
        }
    }

    private static string CreateInviteCode()
    {
        Span<byte> bytes = stackalloc byte[9];
        RandomNumberGenerator.Fill(bytes);
        return Convert.ToBase64String(bytes)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
    }

    /// <summary>
    /// Public HTTPS URL shown to users. Prefer config; otherwise derive from the current request.
    /// Deep link scheme stays internal (landing page redirects to it).
    /// </summary>
    private string ResolvePublicShareBase()
    {
        string? configured = _configuration.GetValue<string>("Invite:PublicShareBase");
        if (!string.IsNullOrWhiteSpace(configured))
            return configured.EndsWith('/') ? configured : configured + "/";

        HttpContext? http = _httpContextAccessor.HttpContext;
        if (http != null)
        {
            string basePath = _configuration.GetValue<string>("BasePath") ?? "vigia";
            basePath = basePath.Trim('/');
            return $"{http.Request.Scheme}://{http.Request.Host}/{basePath}/i/";
        }

        string deepLinkBase = _configuration.GetValue<string>("Invite:DeepLinkBase") ?? "vigia://invite/";
        return deepLinkBase.EndsWith('/') ? deepLinkBase : deepLinkBase + "/";
    }
}
