using System.Text.Json.Serialization;

namespace Vigia.Fiware.Models.SubscriptionDTOs;

public class OrionSubscriptionNotificationDTO
{
    [JsonPropertyName("http")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public OrionSubscriptionHttpDTO? Http { get; set; }

    [JsonPropertyName("httpCustom")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public OrionSubscriptionHttpCustomDTO? HttpCustom { get; set; }

    [JsonPropertyName("attrs")]
    public List<string> Attrs { get; set; } = [];

    [JsonPropertyName("attrsFormat")]
    public string AttrsFormat { get; set; } = "normalized";

    [JsonIgnore]
    public string ResolvedUrl =>
        !string.IsNullOrWhiteSpace(HttpCustom?.Url) ? HttpCustom.Url : Http?.Url ?? string.Empty;

    [JsonIgnore]
    public string? AuthorizationHeader =>
        HttpCustom?.Headers is null
            ? null
            : HttpCustom.Headers.TryGetValue("Authorization", out string? value) ? value : null;
}
