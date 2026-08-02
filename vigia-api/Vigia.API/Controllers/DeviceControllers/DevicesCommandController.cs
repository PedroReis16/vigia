using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Models.Enums;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/{deviceId}/command")]
[Authorize]
public class DevicesCommandController(IDeviceCommandsService service) : ControllerBase
{

    private readonly IDeviceCommandsService _service = service;


    /// <summary>
    /// Envia um comando que será direcionado para o dispositivo
    /// </summary>
    /// <param name="deviceId">Identificador do dispositivo</param>
    /// <param name="command">Comando a ser enviado para o dispositivo</param>
    /// <returns></returns>
    [HttpPatch]
    public async Task<IActionResult> PostCommand(Guid deviceId, [FromBody] DeviceCommandDTO command)
    {
        try
        {
            Guid userId = User.GetUserId();
            await _service.SendCommandAsync(deviceId, userId, command);
            return NoContent();
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception)
        {
            throw;
        }
    }


}