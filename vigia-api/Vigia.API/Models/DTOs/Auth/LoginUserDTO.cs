namespace Vigia.API.Models.DTOs.Auth;

public record LoginUserDTO(
    string Email,
    string Password
);