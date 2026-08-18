using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.SubscriptionDTOs;

public class OrionSubscriptionNotificationDTO
{
    [JsonPropertyName("http")]
    public OrionSubscriptionHttpDTO Http { get; set; } = new();

    [JsonPropertyName("attrs")]
    public List<string> Attrs { get; set; } = [];

    [JsonPropertyName("attrsFormat")]
    public string AttrsFormat { get; set; } = "normalized";
}
