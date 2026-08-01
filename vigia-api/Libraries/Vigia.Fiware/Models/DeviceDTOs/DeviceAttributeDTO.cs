using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.DeviceDTOs;

public class DeviceAttributeDTO
{
    [JsonPropertyName("object_id")]
    [JsonRequired]
    public string ObjectId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    [JsonRequired]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    [JsonRequired]
    public string Type { get; set; } = string.Empty;
}