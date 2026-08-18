using System.Text.Json;
using System.Text.Json.Serialization;

namespace Vigia.API.Models.DTOs.Alerts;

public class OrionAlertNotificationDTO
{
    [JsonPropertyName("subscriptionId")]
    public string SubscriptionId { get; set; } = string.Empty;

    [JsonPropertyName("data")]
    public List<OrionAlertEntityDTO> Data { get; set; } = [];
}

public class OrionAlertEntityDTO
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonExtensionData]
    public Dictionary<string, JsonElement> Attributes { get; set; } = [];
}
