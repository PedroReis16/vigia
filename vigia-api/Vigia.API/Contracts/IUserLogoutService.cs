using Vigia.API.Models.DTOs.Users;

namespace Vigia.API.Contracts;

public interface IUserLogoutService
{
    Task<LogoutResponseDTO> LogoutAsync(
        Guid userId,
        string? clientId,
        LogoutRequestDTO request,
        CancellationToken cancellationToken = default);
}
