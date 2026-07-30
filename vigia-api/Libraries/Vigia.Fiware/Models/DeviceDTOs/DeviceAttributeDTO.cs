using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.DeviceDTOs;

public class DeviceAttributeDTO
{
    [JsonPropertyName("object_id")]
    public string ObjectId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;
}