using System.Text.RegularExpressions;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services.Users;

internal static partial class ProfileFieldRules
{
    public static string RequireName(string? value, string field)
    {
        string name = value?.Trim() ?? string.Empty;
        if (name.Length is < 1 or > 64 || name.Any(char.IsControl) || name.Contains('<') || name.Contains('>'))
            throw new EntityValidationException(field, "Informe um nome válido", ErrorCodes.INVALID_PROFILE_NAME);

        return name;
    }

    public static string RequirePhone(string? value)
    {
        string phone = value?.Trim() ?? string.Empty;
        if (!PhonePattern().IsMatch(phone))
            throw new EntityValidationException("phone", "Informe um telefone válido", ErrorCodes.INVALID_PROFILE_PHONE);

        return phone;
    }

    [GeneratedRegex(@"^[0-9+() .-]{8,16}$", RegexOptions.CultureInvariant)]
    private static partial Regex PhonePattern();
}
