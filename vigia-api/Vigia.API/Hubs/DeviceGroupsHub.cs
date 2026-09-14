using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.SignalR;

namespace Vigia.API.Hubs;

[Authorize(AuthenticationSchemes = "OAuth")]
public class DeviceGroupsHub : Hub
{
    public override async Task OnConnectedAsync()
    {
        string? userId = ResolveUserId(Context.User);
        if (!string.IsNullOrEmpty(userId))
            await Groups.AddToGroupAsync(Context.ConnectionId, UserGroupName(userId));

        await base.OnConnectedAsync();
    }

    public static string UserGroupName(string userId) => $"user:{userId}";

    public static string? ResolveUserId(ClaimsPrincipal? user)
    {
        if (user == null) return null;

        return user.FindFirstValue(JwtRegisteredClaimNames.Sub)
            ?? user.FindFirstValue(ClaimTypes.NameIdentifier)
            ?? user.FindFirstValue("sub");
    }
}

/// <summary>
/// Maps SignalR connections to the JWT <c>sub</c> claim so
/// <see cref="IHubClients.User(string)"/> also works as a fallback.
/// </summary>
public class JwtUserIdProvider : IUserIdProvider
{
    public string? GetUserId(HubConnectionContext connection) =>
        DeviceGroupsHub.ResolveUserId(connection.User);
}
