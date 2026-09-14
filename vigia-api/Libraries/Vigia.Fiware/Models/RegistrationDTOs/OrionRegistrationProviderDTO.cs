using System.Text.Json.Serialization;
namespace Vigia.Fiware.Models.RegistrationDTOs;

public class OrionRegistrationProviderDTO
{
    [JsonPropertyName("http")]
    public OrionRegistrationHttpProviderDTO Http { get; set; } = new();

    [JsonPropertyName("legacyForwarding")]
    public bool LegacyForwarding { get; set; } = true;
}
