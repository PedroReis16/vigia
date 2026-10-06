using Vigia.Models.Enums;

namespace Vigia.Models.Entities;

public class DeviceClip : BaseEntity
{
    public Guid DeviceId { get; set; }
    public Device? Device { get; set; }
    public ClipStatus Status { get; set; } = ClipStatus.Receiving;
    public int FrameCount { get; set; }
    public int Fps { get; set; }
    public string? ObjectKey { get; set; }
}
