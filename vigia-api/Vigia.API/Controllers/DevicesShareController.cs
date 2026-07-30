using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Vigia.API.Controllers;

[ApiController]
[Route("devices/{deviceId}/share")]
[Authorize]
public class DeviceShareController() : ControllerBase
{

    /// <summary>
    /// Gera um link de compartilhamento para um dispositivo para outros usuários
    /// </summary>
    /// <param name="deviceId"></param>
    /// <returns></returns>
    [HttpGet("generate")]
    public async Task<IActionResult> ShareDevice(Guid deviceId)
    {
        return Ok();
    }

    /// <summary>
    /// Confirmação de compartilhamento de um dispositivo entre usuários
    /// </summary>
    /// <param name="deviceId"></param>
    /// <returns></returns>
    [HttpPost("accept")]
    public async Task<IActionResult> AcceptDeviceShare(Guid deviceId)
    {
        return Ok();
    }
}