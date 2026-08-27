using Vigia.API.Models.DTOs.Realtime;

namespace Vigia.API.Contracts;

public interface IGroupRealtimeNotifier
{
    Task NotifyMembershipJoinedAsync(Guid groupId, Guid userId);
    Task NotifyMembershipRemovedAsync(Guid groupId, Guid userId);
}
