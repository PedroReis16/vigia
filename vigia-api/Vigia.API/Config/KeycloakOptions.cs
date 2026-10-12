namespace Vigia.API.Config;

public class KeycloakOptions
{
    public const string SectionName = "Keycloak";

    /// <summary>OIDC discovery URL (rede interna no Docker).</summary>
    public string MetadataAddress { get; set; } = string.Empty;

    /// <summary>Issuer público do realm (browser / access token iss).</summary>
    public string ValidIssuer { get; set; } = string.Empty;

    public string Audience { get; set; } = string.Empty;

    public string[] AdditionalValidIssuers { get; set; } = [];

    /// <summary>
    /// Base do realm para revogar refresh tokens (logout).
    /// Deve usar o mesmo host do <c>iss</c> do token (ex.: Traefik :81).
    /// Se vazio, usa <see cref="ValidIssuer"/>.
    /// Não use o hostname interno Docker (<c>keycloak:8080</c>) — o Keycloak
    /// rejeita o refresh com "Invalid token issuer".
    /// </summary>
    public string? LogoutRealmBaseUrl { get; set; }

    public string ResolveLogoutRealmBaseUrl()
    {
        if (!string.IsNullOrWhiteSpace(LogoutRealmBaseUrl))
            return LogoutRealmBaseUrl.TrimEnd('/');

        return ResolvePublicRealmBaseUrl();
    }

    public string ResolvePublicRealmBaseUrl()
    {
        if (string.IsNullOrWhiteSpace(ValidIssuer))
            throw new InvalidOperationException("Keycloak:ValidIssuer é obrigatório.");

        return ValidIssuer.TrimEnd('/');
    }

    /// <summary>
    /// Host header alinhado ao <c>iss</c> do token (ex.: <c>localhost:81</c>),
    /// para o Keycloak validar o refresh mesmo quando a URL de rede é
    /// <c>host.docker.internal</c>.
    /// </summary>
    public string? ResolveLogoutHostHeader()
    {
        if (!Uri.TryCreate(ResolvePublicRealmBaseUrl(), UriKind.Absolute, out Uri? issuer))
            return null;

        return issuer.IsDefaultPort ? issuer.Host : $"{issuer.Host}:{issuer.Port}";
    }
}
