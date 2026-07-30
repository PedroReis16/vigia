using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models;


public class IotAgentServicePayloadDTO
{
    [JsonPropertyName("apikey")]
    public string ApiKey { get; set; } = string.Empty;

    [JsonPropertyName("entity_type")]
    public string EntityType { get; set; } = string.Empty;

    [JsonPropertyName("resource")]
    public string Resource { get; set; } = string.Empty;
}
