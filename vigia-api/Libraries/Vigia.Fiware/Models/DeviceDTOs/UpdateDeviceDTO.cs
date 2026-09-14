using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.DeviceDTOs;

public class UpdateDeviceDTO
{
    [JsonPropertyName("entity_name")]
    public string EntityName { get; set; } = string.Empty;

    [JsonPropertyName("entity_type")]
    public string EntityType { get; set; } = string.Empty;

    [JsonPropertyName("protocol")]
    public string Protocol { get; set; } = string.Empty;

    [JsonPropertyName("transport")]
    public string Transport { get; set; } = string.Empty;

    [JsonPropertyName("commands")]
    public List<DeviceCommandDTO> Commands { get; set; } = [];

    [JsonPropertyName("attributes")]
    public List<DeviceAttributeDTO> Attributes { get; set; } = [];
}
