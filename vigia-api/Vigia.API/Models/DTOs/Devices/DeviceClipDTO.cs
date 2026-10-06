using Vigia.Models.Enums;

namespace Vigia.API.Models.DTOs.Devices;

public class DeviceClipDTO
{
    public Guid Id { get; set; }
    public Guid DeviceId { get; set; }
    public ClipStatus Status { get; set; }
    public int FrameCount { get; set; }
    public int Fps { get; set; }
    public DateTime CreatedAt { get; set; }
}
