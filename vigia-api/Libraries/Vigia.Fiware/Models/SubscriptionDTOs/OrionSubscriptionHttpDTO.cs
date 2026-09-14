using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.SubscriptionDTOs;

public class OrionSubscriptionHttpDTO
{
    [JsonPropertyName("url")]
    public string Url { get; set; } = string.Empty;
}
