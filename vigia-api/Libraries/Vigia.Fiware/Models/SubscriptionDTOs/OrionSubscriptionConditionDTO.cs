using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.SubscriptionDTOs;

public class OrionSubscriptionConditionDTO
{
    [JsonPropertyName("attrs")]
    public List<string> Attrs { get; set; } = [];

    [JsonPropertyName("expression")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public OrionSubscriptionExpressionDTO? Expression { get; set; }
}
