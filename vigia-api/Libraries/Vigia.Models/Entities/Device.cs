namespace Vigia.Models.Entities;

public class Device : BaseEntity
{
    public string DeviceName { get; set; } = null!;
    public string? Nickname { get; set; }
    public string PublicKey { get; set; } = null!;

    public UserGroup? UserGroup { get; set; } = null!;
}