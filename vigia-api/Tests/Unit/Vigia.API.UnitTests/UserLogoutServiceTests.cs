using Microsoft.EntityFrameworkCore;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Users;
using Vigia.API.Services;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.UnitTests;

public class UserLogoutServiceTests
{
    [Fact]
    public async Task LogoutAsync_WhenKeycloakAccepts_DeletesPushTokenAndReturnsEndSessionUrl()
    {
        await using VigiaDbContext context = CreateContext();
        Guid userId = Guid.NewGuid();
        await SeedUserWithPushToken(context, userId, "fcm-device-1");

        FakeKeycloakSessionClient keycloak = new(revokeResult: true)
        {
            EndSessionUrl = "http://localhost/auth/realms/vigia/protocol/openid-connect/logout?x=1",
        };
        UserLogoutService service = CreateService(context, keycloak);

        LogoutResponseDTO result = await service.LogoutAsync(
            userId,
            "vigia-web",
            new LogoutRequestDTO(
                "refresh-token",
                "fcm-device-1",
                "id-token",
                "http://localhost/"));

        Assert.Equal(keycloak.EndSessionUrl, result.EndSessionUrl);
        Assert.Equal("vigia-web", keycloak.LastClientId);
        Assert.Equal("refresh-token", keycloak.LastRefreshToken);

        UserPushToken token = await context.UserPushTokens.SingleAsync(t => t.Token == "fcm-device-1");
        Assert.NotNull(token.DeletedAt);
    }

    [Fact]
    public async Task LogoutAsync_WhenKeycloakRejects_KeepsPushToken()
    {
        await using VigiaDbContext context = CreateContext();
        Guid userId = Guid.NewGuid();
        await SeedUserWithPushToken(context, userId, "fcm-device-1");

        UserLogoutService service = CreateService(context, new FakeKeycloakSessionClient(revokeResult: false));

        HttpResponseException ex = await Assert.ThrowsAsync<HttpResponseException>(() =>
            service.LogoutAsync(
                userId,
                "vigia-app",
                new LogoutRequestDTO("refresh-token", "fcm-device-1")));

        Assert.Equal(ErrorCodes.KEYCLOAK_LOGOUT_REJECTED, ex.ErrorCode);

        UserPushToken token = await context.UserPushTokens.SingleAsync(t => t.Token == "fcm-device-1");
        Assert.Null(token.DeletedAt);
    }

    [Fact]
    public async Task LogoutAsync_WithoutPushToken_StillRevokesSession()
    {
        await using VigiaDbContext context = CreateContext();
        FakeKeycloakSessionClient keycloak = new(revokeResult: true);
        UserLogoutService service = CreateService(context, keycloak);

        LogoutResponseDTO result = await service.LogoutAsync(
            Guid.NewGuid(),
            "vigia-web",
            new LogoutRequestDTO("refresh-token"));

        Assert.Null(result.EndSessionUrl);
        Assert.Equal("refresh-token", keycloak.LastRefreshToken);
    }

    [Fact]
    public async Task LogoutAsync_MissingRefreshToken_ThrowsValidation()
    {
        await using VigiaDbContext context = CreateContext();
        UserLogoutService service = CreateService(context, new FakeKeycloakSessionClient(revokeResult: true));

        EntityValidationException ex = await Assert.ThrowsAsync<EntityValidationException>(() =>
            service.LogoutAsync(Guid.NewGuid(), "vigia-web", new LogoutRequestDTO(" ")));

        Assert.Equal(ErrorCodes.REFRESH_TOKEN_REQUIRED, ex.ErrorCode);
    }

    [Fact]
    public async Task LogoutAsync_MissingClientId_ThrowsValidation()
    {
        await using VigiaDbContext context = CreateContext();
        UserLogoutService service = CreateService(context, new FakeKeycloakSessionClient(revokeResult: true));

        EntityValidationException ex = await Assert.ThrowsAsync<EntityValidationException>(() =>
            service.LogoutAsync(Guid.NewGuid(), null, new LogoutRequestDTO("refresh-token")));

        Assert.Equal(ErrorCodes.KEYCLOAK_CLIENT_REQUIRED, ex.ErrorCode);
    }

    private static UserLogoutService CreateService(VigiaDbContext context, IKeycloakSessionClient keycloak)
    {
        return new UserLogoutService(
            keycloak,
            new UserPushTokenService(new UserPushTokenDao(context)));
    }

    private static async Task SeedUserWithPushToken(VigiaDbContext context, Guid userId, string token)
    {
        context.Users.Add(new User
        {
            Id = userId,
            Email = "user@vigia.test",
            Phone = "11999990000",
        });
        context.UserPushTokens.Add(new UserPushToken
        {
            Id = Guid.NewGuid(),
            UserId = userId,
            Token = token,
            Platform = "android",
        });
        await context.SaveChangesAsync();
    }

    private static VigiaDbContext CreateContext()
    {
        DbContextOptions<VigiaDbContext> options = new DbContextOptionsBuilder<VigiaDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        VigiaDbContext context = new(options);
        context.Database.EnsureCreated();
        return context;
    }

    private sealed class FakeKeycloakSessionClient(bool revokeResult) : IKeycloakSessionClient
    {
        public string? EndSessionUrl { get; set; }
        public string? LastClientId { get; private set; }
        public string? LastRefreshToken { get; private set; }

        public Task<bool> RevokeRefreshTokenAsync(
            string clientId,
            string refreshToken,
            CancellationToken cancellationToken = default)
        {
            LastClientId = clientId;
            LastRefreshToken = refreshToken;
            return Task.FromResult(revokeResult);
        }

        public string? BuildEndSessionUrl(string? idToken, string? postLogoutRedirectUri)
        {
            if (string.IsNullOrWhiteSpace(idToken) || string.IsNullOrWhiteSpace(postLogoutRedirectUri))
                return null;

            return EndSessionUrl;
        }
    }
}
