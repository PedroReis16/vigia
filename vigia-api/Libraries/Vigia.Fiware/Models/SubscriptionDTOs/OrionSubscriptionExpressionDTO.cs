using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.SubscriptionDTOs;

public class OrionSubscriptionExpressionDTO
{
    [JsonPropertyName("q")]
    public string Q { get; set; } = string.Empty;
}
