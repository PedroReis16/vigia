using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.DeviceDTOs;

public class NewDeviceDTO
{
    [JsonPropertyName("device_id")]
    public Guid DeviceId { get; set; }

    [JsonPropertyName("entity_name")]
    public string EntityName { get; set; } = string.Empty;

    [JsonPropertyName("entity_type")]
    public string EntityType { get; set; } = string.Empty;

    [JsonPropertyName("protocol")]
    public string Protocol { get; set; } = string.Empty;

    [JsonPropertyName("transport")]
    public string Transport { get; set; } = string.Empty;

    [JsonPropertyName("attributes")]
    public List<DeviceAttributeDTO> Attributes { get; set; } = [];

    [JsonPropertyName("commands")]
    public List<DeviceCommandDTO> Commands { get; set; } = [];
}