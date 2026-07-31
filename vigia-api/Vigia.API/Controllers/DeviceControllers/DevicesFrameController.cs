using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/{deviceId}/frame")]
[Authorize]
public class DevicesFrameController(IDevicesService devicesService) : ControllerBase
{
    private readonly IDevicesService _devicesService = devicesService;

    /// <summary>
    /// Enviar um frame atual do dispositivo
    /// </summary>
    /// <param name="deviceId"></param>
    /// <param name="frameFile"></param>
    /// <returns></returns>
    [HttpPost]
    [Consumes("multipart/form-data")]
    [ProducesResponseType(StatusCodes.Status202Accepted)]
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
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public IActionResult GetLastFrame(Guid deviceId)
    {
        byte[]? frameBytes = _devicesService.GetDeviceFrame(deviceId);
        if (frameBytes == null || frameBytes.Length == 0)
            return NoContent();

        return File(frameBytes, "image/jpeg");
    }
}
