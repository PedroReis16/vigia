using Microsoft.AspNetCore.SignalR;
using Vigia.API.Contracts;
using Vigia.API.Hubs;
using Vigia.API.Models.DTOs.Realtime;
using Vigia.Database.Contracts;

namespace Vigia.API.Services;

public class GroupRealtimeNotifier(
    IHubContext<DeviceGroupsHub> hubContext,
    IServiceScopeFactory scopeFactory,
    ILogger<GroupRealtimeNotifier> logger) : IGroupRealtimeNotifier
{
    public const string MembershipChangedEvent = "GroupMembershipChanged";

    private readonly IHubContext<DeviceGroupsHub> _hubContext = hubContext;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;
    private readonly ILogger<GroupRealtimeNotifier> _logger = logger;

    public Task NotifyMembershipJoinedAsync(Guid groupId, Guid userId) =>
        NotifyAsync(groupId, userId, "joined");

    public Task NotifyMembershipRemovedAsync(Guid groupId, Guid userId) =>
        NotifyAsync(groupId, userId, "removed");

    private async Task NotifyAsync(Guid groupId, Guid affectedUserId, string changeType)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            IUserDao userDao = scope.ServiceProvider.GetRequiredService<IUserDao>();
            IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();

            List<Guid> memberIds = (await userDao.GetUsersByGroupAsync(groupId))
                .Select(u => u.Id)
                .ToList();

            if (!memberIds.Contains(affectedUserId))
                memberIds.Add(affectedUserId);

            List<Guid> deviceIds = await devicesDao.GetDeviceIdsByGroupAsync(groupId);

            GroupMembershipChangedDTO payload = new()
            {
                GroupId = groupId,
                AffectedUserId = affectedUserId,
                ChangeType = changeType,
                DeviceIds = deviceIds,
            };

            // Prefer explicit per-user SignalR groups (joined in OnConnectedAsync).
            // Also fan-out via Clients.User as a secondary path.
            foreach (Guid memberId in memberIds)
            {
                string key = memberId.ToString();
                await _hubContext.Clients
                    .Group(DeviceGroupsHub.UserGroupName(key))
                    .SendAsync(MembershipChangedEvent, payload);
                await _hubContext.Clients
                    .User(key)
                    .SendAsync(MembershipChangedEvent, payload);
            }

            _logger.LogInformation(
                "SignalR {Event} group={GroupId} user={UserId} type={ChangeType} recipients={Count} devices={DeviceCount}",
                MembershipChangedEvent, groupId, affectedUserId, changeType, memberIds.Count, deviceIds.Count);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Falha ao notificar alteração de membros do grupo {GroupId}", groupId);
        }
    }
}
