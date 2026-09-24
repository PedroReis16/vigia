using Vigia.Fiware.Models.RegistrationDTOs;

namespace Vigia.Fiware.Services;

/// <summary>
/// Helpers para registrations de comando no Orion.
/// A URL do provider deve ser o norte NGSI do IoT Agent (porta 4041),
/// não o path admin exposto no Traefik (<c>/vigia/fiware/iot</c>).
/// </summary>
internal static class OrionRegistrationSync
{
    public const string DefaultProviderUrl = "http://iot-agent:4041";
    public const string ProviderUrlConfigKey = "Fiware:ProviderUrl";

    public static string ResolveProviderUrl(string? configured)
    {
        if (!string.IsNullOrWhiteSpace(configured))
            return configured.Trim().TrimEnd('/');

        return DefaultProviderUrl;
    }

    public static bool IsForEntity(
        OrionRegistrationDTO registration,
        string entityName,
        string entityType)
    {
        return registration.DataProvided.Entities.Any(entity =>
            string.Equals(entity.Id, entityName, StringComparison.Ordinal)
            && string.Equals(entity.Type, entityType, StringComparison.Ordinal));
    }

    public static bool HasProviderUrl(OrionRegistrationDTO registration, string providerUrl)
    {
        string current = registration.Provider.Http.Url?.Trim().TrimEnd('/') ?? string.Empty;
        return string.Equals(current, providerUrl.TrimEnd('/'), StringComparison.OrdinalIgnoreCase);
    }

    public static bool AttrsMatch(IEnumerable<string> current, IEnumerable<string> expected)
    {
        HashSet<string> currentAttrs = current.ToHashSet(StringComparer.Ordinal);
        HashSet<string> expectedAttrs = expected.ToHashSet(StringComparer.Ordinal);
        return currentAttrs.SetEquals(expectedAttrs);
    }

    public static OrionRegistrationDTO? FindCanonical(
        IEnumerable<OrionRegistrationDTO> registrations,
        string entityName,
        string entityType,
        string providerUrl,
        IReadOnlyCollection<string> expectedAttrs)
    {
        return registrations.FirstOrDefault(registration =>
            IsForEntity(registration, entityName, entityType)
            && HasProviderUrl(registration, providerUrl)
            && AttrsMatch(registration.DataProvided.Attrs, expectedAttrs));
    }
}
