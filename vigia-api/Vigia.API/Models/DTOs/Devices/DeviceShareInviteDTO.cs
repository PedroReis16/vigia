namespace Vigia.API.Models.DTOs.Devices;

public class DeviceShareInviteDTO
{
    public string Token { get; set; } = null!;
    public string InviteUrl { get; set; } = null!;
    public DateTime ExpiresAt { get; set; }
}
