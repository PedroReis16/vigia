using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.DeviceDTOs;

public class DeviceCommandDTO
{
    [JsonPropertyName("name")]
    [JsonRequired]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    [JsonRequired]
    public string Type { get; set; } = string.Empty;
}