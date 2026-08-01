namespace Vigia.API.Models.DTOs.Realtime;

public class GroupMembershipChangedDTO
{
    public Guid GroupId { get; set; }
    public Guid AffectedUserId { get; set; }
    public string ChangeType { get; set; } = null!; // joined | removed
    public List<Guid> DeviceIds { get; set; } = [];
}
