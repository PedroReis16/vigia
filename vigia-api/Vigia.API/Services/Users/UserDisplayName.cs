namespace Vigia.API.Services.Users;

internal static class UserDisplayName
{
    public static string Format(string? firstName, string? lastName, string? email)
    {
        string name = string.Join(
            ' ',
            new[] { firstName, lastName }.Where(part => !string.IsNullOrWhiteSpace(part))).Trim();

        if (!string.IsNullOrWhiteSpace(name))
            return name;

        return email?.Trim() ?? string.Empty;
    }
}
