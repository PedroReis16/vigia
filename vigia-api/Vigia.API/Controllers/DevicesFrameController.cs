using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Vigia.API.Controllers;

[ApiController]
[Route("devices/{deviceId}/frame")]
[Authorize]
public class DevicesFrameController() : ControllerBase
{
    /// <summary>
    /// Enviar um frame atual do dispositivo
    /// </summary>
    /// <param name="deviceId"></param>
    /// <param name="frameFile"></param>
    /// <returns></returns>
    [HttpPost]
    [Consumes("multipart/form-data")]
    public async Task<IActionResult> PostFrame(Guid deviceId, IFormFile frameFile)
    {
        return Ok();
    }

    /// <summary>
    /// Obter o último frame enviado do dispositivo
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> GetLastFrame(Guid deviceId)
    {
        return Ok();
    }
}