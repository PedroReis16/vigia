using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models;

public class NewIotServiceDTO
{
    [JsonPropertyName("services")]
    public List<IotAgentServicePayloadDTO> Services { get; set; } = [];
}