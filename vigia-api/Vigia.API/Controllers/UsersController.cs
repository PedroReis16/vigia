using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Users;

namespace Vigia.API.Controllers;

[ApiController]
[Route("users")]
[Authorize]
public class UserController(
    IUserPushTokenService pushTokenService,
    IUserLogoutService logoutService) : ControllerBase
{
    private readonly IUserPushTokenService _pushTokenService = pushTokenService;
    private readonly IUserLogoutService _logoutService = logoutService;

    /// <summary>
    /// Registra ou atualiza o token FCM do aparelho do usuário autenticado.
    /// </summary>
    [HttpPut("push-token")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public async Task<IActionResult> UpsertPushToken([FromBody] UpsertPushTokenDTO dto)
    {
        Guid userId = User.GetUserId();
        await _pushTokenService.UpsertPushTokenAsync(userId, dto.Token, dto.Platform);
        return NoContent();
    }

    /// <summary>
    /// Remove o token FCM do aparelho (ex.: logout parcial / limpeza local).
    /// </summary>
    [HttpDelete("push-token")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public async Task<IActionResult> DeletePushToken([FromBody] DeletePushTokenDTO dto)
    {
        Guid userId = User.GetUserId();
        await _pushTokenService.DeletePushTokenAsync(userId, dto.Token);
        return NoContent();
    }

    /// <summary>
    /// Encerra a sessão no Keycloak e, se aceito, remove o push token deste aparelho.
    /// </summary>
    [HttpPost("logout")]
    [ProducesResponseType(typeof(LogoutResponseDTO), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<LogoutResponseDTO>> Logout(
        [FromBody] LogoutRequestDTO dto,
        CancellationToken cancellationToken)
    {
        LogoutResponseDTO result = await _logoutService.LogoutAsync(
            User.GetUserId(),
            User.GetAuthorizedParty(),
            dto,
            cancellationToken);

        return Ok(result);
    }
}
