using Vigia.Models.Enums;

namespace Vigia.API.Models.DTOs.Devices;

public class DeviceDTO
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Nickname { get; set; }
    public DeviceRooms? Room { get; set; }
    public Guid? OwnerId { get; set; }
    public string MacAddress { get; set; } = string.Empty;
    public string? ThumbnailUrl { get; set; }
    public bool IsRunning { get; set; }
    public bool IsClipsEnabled { get; set; }
}