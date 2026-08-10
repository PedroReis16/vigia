using System.Text.Json.Serialization;


namespace Vigia.Fiware.Models.RegistrationDTOs;

public class OrionRegistrationHttpProviderDTO
{
    [JsonPropertyName("url")]
    public string Url { get; set; } = string.Empty;
}