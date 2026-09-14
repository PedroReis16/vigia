using System.Text.Json.Serialization;
using Vigia.Fiware.Models.RegistrationDTOs;

namespace Vigia.Fiware.Models.SubscriptionDTOs;

public class OrionSubscriptionSubjectDTO
{
    [JsonPropertyName("entities")]
    public List<OrionRegistrationEntityDTO> Entities { get; set; } = [];

    [JsonPropertyName("condition")]
    public OrionSubscriptionConditionDTO Condition { get; set; } = new();
}
