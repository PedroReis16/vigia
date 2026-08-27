using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts.Devices;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices")]
[Authorize]
public class DeviceShareController(IDeviceShareService service) : ControllerBase
{
    private readonly IDeviceShareService _service = service;

    /// <summary>
    /// Gera um link de compartilhamento para o grupo do dispositivo
    /// </summary>
    [HttpGet("{deviceId:guid}/share/generate")]
    public async Task<IActionResult> GenerateShareLink(Guid deviceId)
    {
        try
        {
            Guid userId = User.GetUserId();
            DeviceShareInviteDTO invite = await _service.GenerateInviteAsync(deviceId, userId);
            return Ok(invite);
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception) { throw; }
    }

    /// <summary>
    /// Aceita um convite de compartilhamento e vincula o usuário autenticado ao grupo
    /// </summary>
    [HttpPost("share/accept")]
    public async Task<IActionResult> AcceptDeviceShare([FromBody] AcceptDeviceShareDTO body)
    {
        try
        {
            Guid userId = User.GetUserId();
            await _service.AcceptInviteAsync(body.Token, userId);
            return Ok(new { message = "Convite aceito com sucesso" });
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception) { throw; }
    }
}
