namespace Vigia.Models.Entities;

public class UserPushToken : BaseEntity
{
    public Guid UserId { get; set; }
    public string Token { get; set; } = null!;
    public string Platform { get; set; } = null!;
}
