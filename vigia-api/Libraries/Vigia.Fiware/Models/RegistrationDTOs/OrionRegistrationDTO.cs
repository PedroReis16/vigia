using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.RegistrationDTOs;

public class OrionRegistrationDTO
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("dataProvided")]
    public OrionRegistrationDataProvidedDTO DataProvided { get; set; } = new();

    [JsonPropertyName("provider")]
    public OrionRegistrationProviderDTO Provider { get; set; } = new();
}

