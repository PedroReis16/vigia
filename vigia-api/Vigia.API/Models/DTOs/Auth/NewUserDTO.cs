namespace Vigia.API.Models.DTOs.Auth;

public record NewUserDTO(
    string Name,
    string Email,
    string Password
);