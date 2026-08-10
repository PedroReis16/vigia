namespace Vigia.API.Models.DTOs.Auth;

public record AuthResponseDTO(
    string AccessToken,
    string RefreshToken
);