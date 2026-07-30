using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.DeviceDTOs;

public class IotAgentDevicesResponseDTO
{
    [JsonPropertyName("count")]
    public int Count { get; set; }

    [JsonPropertyName("devices")]
    public List<IotAgentDeviceDTO> Devices { get; set; } = [];
}

public class IotAgentDeviceDTO
{
    [JsonPropertyName("device_id")]
    public string DeviceId { get; set; } = string.Empty;

    [JsonPropertyName("entity_name")]
    public string EntityName { get; set; } = string.Empty;

    [JsonPropertyName("entity_type")]
    public string EntityType { get; set; } = string.Empty;

    [JsonPropertyName("protocol")]
    public string? Protocol { get; set; }

    [JsonPropertyName("transport")]
    public string? Transport { get; set; }

    [JsonPropertyName("attributes")]
    public List<DeviceAttributeDTO> Attributes { get; set; } = [];

    [JsonPropertyName("commands")]
    public List<DeviceCommandDTO> Commands { get; set; } = [];
}

public class UpdateDeviceSchemaDTO
{
    [JsonPropertyName("attributes")]
    public List<DeviceAttributeDTO> Attributes { get; set; } = [];

    [JsonPropertyName("commands")]
    public List<DeviceCommandDTO> Commands { get; set; } = [];
}

public class NewDevicesRequestDTO
{
    [JsonPropertyName("devices")]
    public List<NewDeviceDTO> Devices { get; set; } = [];
}
