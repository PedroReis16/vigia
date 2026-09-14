namespace Vigia.API.Models.DTOs.Auth;

public record UserCredentialsDTO(
    Guid Id,
    string Name,
    string Email,
    List<string> Roles
);