namespace Vigia.API.Config;

public class FirebaseOptions
{
    public const string SectionName = "Firebase";

    /// <summary>
    /// Service-account JSON as raw JSON or Base64 (preferred in environment variables).
    /// </summary>
    public string CredentialJson { get; set; } = string.Empty;

    public string CredentialPath { get; set; } = string.Empty;
}
