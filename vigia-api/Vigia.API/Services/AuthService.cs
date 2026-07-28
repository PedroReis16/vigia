using System.Security.Cryptography;
using System.Text;
using Vigia.API.Contracts;
using Vigia.API.Database.Contracts;
using Vigia.API.Models.DTOs.Auth;
using Vigia.API.Models.Helpers;
using Vigia.Models.Entities;
using Vigia.Models.Exceptions;
using Vigia.Models.Extensions;
using Vigia.Models.Helpers;

namespace Vigia.API.Services;

internal class AuthService(ILogger<AuthService> logger, IServiceScopeFactory scopeFactory) : IAuthService
{
    private readonly ILogger<AuthService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task<AuthResponseDTO?> LoginUserAsync(LoginUserDTO loginUserDTO, string requestIp)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            IUserDao userDao = scope.ServiceProvider.GetRequiredService<IUserDao>();

            User? user = await userDao.FindUserByEmailAsync(loginUserDTO.Email);

            if (user == null)
                return null;

            byte[] passwordSalt = user.Salt;

            byte[] attemptPasswordHash = PasswordHasher.Hash(loginUserDTO.Password, passwordSalt);

            if (!attemptPasswordHash.SequenceEqual(user.Password))
                return null;

            string accessToken = GenerateAccessToken(scope, user.Id, user.Roles.Select(r => r.Id).ToList());

            string refreshToken = await GenerateRefreshTokenAsync(scope, user.Id, requestIp);

            return new AuthResponseDTO(accessToken, refreshToken);
        }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMessage = $"Houve um erro ao tentar realizar a autenticação do usuário com o email {loginUserDTO.Email}: {ex.GetFullMessage()}";
            _logger.LogError(errorMessage);
            throw new Exception(errorMessage);
        }
    }

    public async Task<AuthResponseDTO?> RefreshTokenAsync(string refreshToken, string requestIp)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            IRefreshTokenDao refreshTokenDao = scope.ServiceProvider.GetRequiredService<IRefreshTokenDao>();

            RefreshToken? trackedToken = await refreshTokenDao.FindByTokenAsync(refreshToken);

            if (trackedToken == null || trackedToken.ExpiresAt < DateTime.UtcNow || trackedToken.RevokedAt != null)
                throw new UnauthorizedAccessException("Token de atualização inválido ou expirado");

            IUserDao userDao = scope.ServiceProvider.GetRequiredService<IUserDao>();

            User? user = await userDao.FindAsync(trackedToken.UserId);

            if (user == null)
                throw new UnauthorizedAccessException("Usuário não encontrado");

            string accessToken = GenerateAccessToken(scope, user.Id, user.Roles.Select(r => r.Id).ToList());

            string newRefreshToken = await GenerateRefreshTokenAsync(scope, user.Id, requestIp);

            await RevokeRefreshTokenAsync(scope, refreshToken, newRefreshToken);

            return new AuthResponseDTO(accessToken, newRefreshToken);
        }
        catch (UnauthorizedAccessException) { throw; }
        catch (Exception ex)
        {
            string errorMessage = $"Houve um erro ao tentar realizar a atualização do token de acesso: {ex.GetFullMessage()}";
            _logger.LogError(errorMessage);
            throw new Exception(errorMessage);
        }
    }

    private async Task RevokeRefreshTokenAsync(IServiceScope scope, string oldRefreshToken, string? newRefreshToken = null)
    {
        IRefreshTokenDao tokenDao = scope.ServiceProvider.GetRequiredService<IRefreshTokenDao>();

        await tokenDao.RevokeTokenAsync(oldRefreshToken, newRefreshToken);

    }

    private string GenerateAccessToken(IServiceScope scope, Guid userId, List<string> roles)
    {
        IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();
        return JwtConverter.Encode(configuration, userId, roles);
    }

    private async Task<string> GenerateRefreshTokenAsync(IServiceScope scope, Guid userId, string requestIp)
    {
        IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();

        IRefreshTokenDao refreshTokenDao = scope.ServiceProvider.GetRequiredService<IRefreshTokenDao>();

        int refreshTokenExpiresIn = configuration.GetValue<int>("JWT:RefreshTokenExpiresIn");

        DateTime expiresAt = DateTime.UtcNow.AddSeconds(refreshTokenExpiresIn);

        byte[] tokenBytes = RandomNumberGenerator.GetBytes(64);
        string token = HashToken(Convert.ToBase64String(tokenBytes));

        RefreshToken refreshToken = new()
        {
            UserId = userId,
            RequestIp = requestIp,
            Token = token,
            ExpiresAt = expiresAt
        };

        await refreshTokenDao.AddAsync(refreshToken);

        return token;
    }

    private string HashToken(string token)
    {
        byte[] bytes = SHA256.HashData(Encoding.UTF8.GetBytes(token));
        return Convert.ToBase64String(bytes);
    }

    public async Task LogoutUserAsync(string refreshToken)
    {
        throw new NotImplementedException();
    }
}