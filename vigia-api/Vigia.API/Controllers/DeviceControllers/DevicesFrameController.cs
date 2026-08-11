using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts.Devices;
using Vigia.Models.Middlewares;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/{deviceId}/frame")]
public class DevicesFrameController(IDevicesService devicesService) : ControllerBase
{
    private readonly IDevicesService _devicesService = devicesService;

    /// <summary>
    /// Enviar um frame atual do dispositivo
    /// </summary>
    [HttpPost]
    [Authorize(AuthenticationSchemes = DeviceSignatureDefaults.AuthenticationScheme)]
    [Consumes("multipart/form-data")]
    [ProducesResponseType(StatusCodes.Status202Accepted)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public IActionResult PostFrame(Guid deviceId, IFormFile frameFile)
    {
        using Stream frameStream = frameFile.OpenReadStream();
        _devicesService.SaveDeviceFrame(deviceId, frameStream);

        return Accepted();
    }

    /// <summary>
    /// Obter o último frame enviado do dispositivo
    /// </summary>
    [HttpGet]
    [Authorize(AuthenticationSchemes = FrameAccessTokenDefaults.AuthenticationScheme)]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public IActionResult GetLastFrame(Guid deviceId)
    {
        byte[]? frameBytes = _devicesService.GetDeviceFrame(deviceId);
        if (frameBytes == null || frameBytes.Length == 0)
            return NoContent();

        return File(frameBytes, "image/jpeg");
    }
}
