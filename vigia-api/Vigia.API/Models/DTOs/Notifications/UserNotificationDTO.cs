namespace Vigia.API.Models.DTOs.Notifications;

public class UserNotificationDTO
{
    public Guid Id { get; set; }
    public Guid EpisodeId { get; set; }
    public Guid DeviceId { get; set; }
    public string Type { get; set; } = "fall";
    public string Title { get; set; } = null!;
    public string Body { get; set; } = null!;
    public DateTime CreatedAt { get; set; }
    public bool Read { get; set; }
    public DateTime? ReadAt { get; set; }
}

public class NotificationListDTO
{
    public List<UserNotificationDTO> Items { get; set; } = [];
    public int UnreadCount { get; set; }
}
