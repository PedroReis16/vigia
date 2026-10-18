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

    /// <summary>Usuário administrador do realm master. Usado para gravar nome, telefone e apagar a conta.</summary>
    public string AdminUsername { get; set; } = string.Empty;

    public string AdminPassword { get; set; } = string.Empty;

    public string AdminClientId { get; set; } = "admin-cli";

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
    /// Origem interna do Keycloak, a partir de <see cref="MetadataAddress"/>
    /// (ex.: <c>http://keycloak:8080/auth</c>).
    /// </summary>
    public string ResolveAdminServerRoot()
    {
        if (string.IsNullOrWhiteSpace(MetadataAddress))
            throw new InvalidOperationException("Keycloak:MetadataAddress é obrigatório.");

        const string marker = "/realms/";
        int index = MetadataAddress.IndexOf(marker, StringComparison.OrdinalIgnoreCase);
        if (index <= 0)
            throw new InvalidOperationException("Keycloak:MetadataAddress precisa incluir /realms/{realm}.");

        return MetadataAddress[..index].TrimEnd('/');
    }

    public string ResolveRealmName()
    {
        string issuer = ResolvePublicRealmBaseUrl();
        int slash = issuer.LastIndexOf('/');
        if (slash < 0 || slash == issuer.Length - 1)
            throw new InvalidOperationException("Keycloak:ValidIssuer precisa terminar com o nome do realm.");

        return issuer[(slash + 1)..];
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
