namespace Vigia.API.Models.DTOs.Users;

public sealed class KeycloakUserSyncMessage
{
    public string Operation { get; set; } = string.Empty;

    public Guid Id { get; set; }

    public string? FirstName { get; set; }

    public string? LastName { get; set; }

    public string? Email { get; set; }

    public string? Phone { get; set; }
}
