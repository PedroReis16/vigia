namespace Vigia.Models.Entities;

public class GroupInvite : BaseEntity
{
    public string Token { get; set; } = null!;
    public Guid GroupId { get; set; }
    public Guid CreatedByUserId { get; set; }
    public DateTime ExpiresAt { get; set; }
    public DateTime? RevokedAt { get; set; }

    public Group Group { get; set; } = null!;
}
