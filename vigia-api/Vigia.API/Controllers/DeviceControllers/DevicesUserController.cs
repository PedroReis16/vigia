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
    [HttpGet]
    public async Task<IActionResult> GetDeviceUsers(Guid deviceId)
    {
        try
        {
            Guid userId = User.GetUserId();
            List<DeviceUserDTO> users = await _service.GetDeviceUsersAsync(deviceId, userId);
            return Ok(users);
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception) { throw; }
    }

    /// <summary>
    /// Remove um usuário do grupo do dispositivo (owner remove outro) ou o próprio usuário sai do grupo
    /// </summary>
    [HttpDelete("{userId:guid}")]
    public async Task<IActionResult> RemoveDeviceUser(Guid deviceId, Guid userId)
    {
        try
        {
            Guid requestingUserId = User.GetUserId();
            await _service.RemoveDeviceUserAsync(deviceId, userId, requestingUserId);
            return Ok(new { message = "Usuário desvinculado do dispositivo com sucesso" });
        }
        catch (UnauthorizedAccessException)
        {
            return Forbid();
        }
        catch (Exception) { throw; }
    }

    /// <summary>
    /// Vincular um dispositivo a um usuário (pareamento / claim de ownership)
    /// </summary>
    [HttpPatch("track")]
    public async Task<IActionResult> TrackDeviceUser(Guid deviceId)
    {
        Guid userId = User.GetUserId();

        // await _service.TrackDeviceUserAsync(deviceId, userId);

        return Ok(new { message = "Dispositivo vinculado ao usuário com sucesso" });
    }

    /// <summary>
    /// Excluir dispositivo do usuário (pareamento / unclaim)
    /// </summary>
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
