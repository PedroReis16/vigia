using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.SubscriptionDTOs;

public class NewOrionSubscriptionDTO
{
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("subject")]
    public OrionSubscriptionSubjectDTO Subject { get; set; } = new();

    [JsonPropertyName("notification")]
    public OrionSubscriptionNotificationDTO Notification { get; set; } = new();
}
