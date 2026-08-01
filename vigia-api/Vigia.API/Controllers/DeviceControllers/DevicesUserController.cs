using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/{deviceId}/users")]
[Authorize]
public class DevicesUsersController(IDeviceUsersService service) : ControllerBase
{
    private readonly IDeviceUsersService _service = service;

    /// <summary>
    /// Listar usuários de um dispositivo
    /// </summary>
    /// <param name="deviceId"></param>
    /// <returns></returns>
    [HttpGet]
    public async Task<IActionResult> GetDeviceUsers(Guid deviceId)
    {
        try
        {
            List<DeviceUserDTO> users = await _service.GetDeviceUsersAsync(deviceId);

            return Ok(users);
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception) { throw; }
    }

    /// <summary>
    /// Gera link de convite para um ou mais usuários para um dispositivo
    /// </summary>
    /// <param name="deviceId"></param>
    [HttpPost("invite")]
    public async Task<IActionResult> GenerateInviteLink(Guid deviceId)
    {
        try
        {
            Guid userId = User.GetUserId();

            // await _service.GenerateInviteLinkAsync(deviceId, userId);

            return Ok(new { message = "Link de convite gerado com sucesso" });
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception) { throw; }
    }

    /// <summary>
    /// Vincular um dispositivo a um usuário
    /// </summary>
    /// <param name="deviceId"></param>
    /// <returns></returns>
    [HttpPatch("track")]
    public async Task<IActionResult> TrackDeviceUser(Guid deviceId)
    {
        Guid userId = User.GetUserId();

        // await _service.TrackDeviceUserAsync(deviceId, userId);

        return Ok(new { message = "Dispositivo vinculado ao usuário com sucesso" });
    }

    ///<summary>
    /// Excluir dispositivo do usuário
    /// </summary>
    /// <param name="deviceId"></param>
    /// <returns></returns>
    [HttpDelete("untrack")]
    public async Task<IActionResult> UntrackDeviceUser(Guid deviceId)
    {
        try
        {
            Guid userId = User.GetUserId();

            // await _service.UntrackedDeviceUserAsync(deviceId, userId);

            return Ok(new { message = "Dispositivo desvinculado do usuário com sucesso" });
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