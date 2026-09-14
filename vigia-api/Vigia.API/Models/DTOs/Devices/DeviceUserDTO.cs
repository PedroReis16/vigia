namespace Vigia.API.Models.DTOs.Devices;

public class DeviceUserDTO
{
    public Guid Id { get; set; }
    public string Name { get; set; } = null!;
    public string? UserPictureUrl { get; set; }
    public bool IsOwner { get; set; }
}