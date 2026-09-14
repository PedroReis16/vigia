using System.Text.Json.Serialization;


namespace Vigia.Fiware.Models.RegistrationDTOs;

public class OrionRegistrationEntityDTO
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;
}