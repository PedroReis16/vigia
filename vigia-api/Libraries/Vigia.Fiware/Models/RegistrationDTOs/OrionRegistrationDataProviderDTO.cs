using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.RegistrationDTOs;

public class OrionRegistrationDataProvidedDTO
{
    [JsonPropertyName("entities")]
    public List<OrionRegistrationEntityDTO> Entities { get; set; } = [];

    [JsonPropertyName("attrs")]
    public List<string> Attrs { get; set; } = [];
}