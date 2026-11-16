namespace Vigia.Models.Entities;

public class UserNotification : BaseEntity
{
    public Guid UserId { get; set; }
    public User? User { get; set; }

    public Guid EpisodeId { get; set; }
    public FallAlertEpisode? Episode { get; set; }

    public Guid DeviceId { get; set; }
    public Device? Device { get; set; }

    public string Type { get; set; } = "fall";
    public string Title { get; set; } = null!;
    public string Body { get; set; } = null!;

    public DateTime? ReadAt { get; set; }
}
