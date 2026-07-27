using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Controllers;

[ApiController]
[Route("[controller]")]
public class DeviceController(IDeviceService service) : ControllerBase
{
    private readonly IDeviceService _service = service;

    /// <summary>
    /// Registra um novo dispositivo no sistema, captando informações de identificação do hardware
    /// </summary>
    /// <returns></returns>
    [HttpPost("register")]
    public async Task<IActionResult> RegisterDevice([FromBody] NewDeviceDTO newDevice)
    {
        await _service.RegisterDeviceAsync(newDevice);

        return CreatedAtAction(nameof(RegisterDevice), new { id = newDevice.Id });
    }
}