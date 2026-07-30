using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.ServiceDTOs;

public class NewIotServiceDTO
{
    [JsonPropertyName("services")]
    public List<IotAgentServicePayloadDTO> Services { get; set; } = [];
}