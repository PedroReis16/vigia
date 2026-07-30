using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.ServiceDTOs;

public class IotAgentServicesResponseDTO
{
    public int Count { get; set; }

    [JsonPropertyName("services")]
    public List<IotAgentServiceDTO> Services { get; set; } = [];
}

public class IotAgentServiceDTO
{
    [JsonPropertyName("_id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("apikey")]
    public string ApiKey { get; set; } = string.Empty;

    public string Service { get; set; } = string.Empty;

    public string Resource { get; set; } = string.Empty;

    [JsonPropertyName("entity_type")]
    public string EntityType { get; set; } = string.Empty;
}


