using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts.Devices;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Models.Enums;
using Vigia.Models.Middlewares;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/{deviceId}/command")]
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
    [Authorize]
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

    /// <summary>
    /// Hook do MediaMTX (runOnDemand when the first reader arrives and nobody is publishing):
    /// envia START_STREAMING sem JWT de usuário. Autenticado por Basic da conta mediamtx.
    /// </summary>
    [HttpPatch("demand")]
    [Authorize(AuthenticationSchemes = ServiceBasicDefaults.AuthenticationScheme, Roles = ServiceBasicDefaults.MediaMtxRole)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> DemandStartStreaming(
        Guid deviceId,
        [FromBody] DeviceCommandDTO? command = null)
    {
        if (command is not null && command.Command != DeviceCommands.START_STREAMING)
            return BadRequest("Somente START_STREAMING é permitido neste endpoint");

        await _service.SendDemandStartStreamingAsync(deviceId);
        return NoContent();
    }

    /// <summary>
    /// Hook do MediaMTX (runOnUnDemand after runOnDemandCloseAfter with no readers):
    /// envia STOP_STREAMING sem JWT de usuário. Autenticado por Basic da conta mediamtx.
    /// </summary>
    [HttpPatch("undemand")]
    [Authorize(AuthenticationSchemes = ServiceBasicDefaults.AuthenticationScheme, Roles = ServiceBasicDefaults.MediaMtxRole)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> UndemandStopStreaming(
        Guid deviceId,
        [FromBody] DeviceCommandDTO? command = null)
    {
        if (command is not null && command.Command != DeviceCommands.STOP_STREAMING)
            return BadRequest("Somente STOP_STREAMING é permitido neste endpoint");

        await _service.SendUndemandStopStreamingAsync(deviceId);
        return NoContent();
    }
}
