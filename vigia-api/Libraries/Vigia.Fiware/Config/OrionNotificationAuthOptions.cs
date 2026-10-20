namespace Vigia.Fiware.Config;

public class OrionNotificationAuthOptions
{
    public const string SectionName = "ServiceBasic:Orion";

    public string Username { get; set; } = "orion";

    public string Password { get; set; } = string.Empty;
}
