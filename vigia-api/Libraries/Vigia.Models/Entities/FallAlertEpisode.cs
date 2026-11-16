using Vigia.Models.Enums;

namespace Vigia.Models.Entities;

public class FallAlertEpisode : BaseEntity
{
    public Guid DeviceId { get; set; }
    public Device? Device { get; set; }

    public Guid GroupId { get; set; }
    public Group? Group { get; set; }

    public AlertEpisodeKind Kind { get; set; } = AlertEpisodeKind.Fall;

    public FallAlertEpisodeStatus Status { get; set; } = FallAlertEpisodeStatus.Active;

    public DateTime FirstDetectedAt { get; set; } = DateTime.UtcNow;
    public DateTime LastNotifiedAt { get; set; } = DateTime.UtcNow;
    public DateTime? NextRetryAt { get; set; }
    public int NotifyCount { get; set; }

    public DateTime? AcknowledgedAt { get; set; }
    public Guid? AcknowledgedByUserId { get; set; }

    public ICollection<UserNotification> Notifications { get; set; } = [];
}
