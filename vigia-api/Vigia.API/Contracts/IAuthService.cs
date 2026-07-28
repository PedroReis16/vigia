using Vigia.API.Models.DTOs.Auth;

namespace Vigia.API.Contracts;

public interface IAuthService
{
    Task<AuthResponseDTO?> LoginUserAsync(LoginUserDTO newUserDTO, string requestIp);
    Task<AuthResponseDTO?> RefreshTokenAsync(string refreshToken, string requestIp);
    Task LogoutUserAsync(string refreshToken);
}