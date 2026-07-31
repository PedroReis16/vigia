using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/{deviceId}/command")]
[Authorize]
public class DevicesCommandController : ControllerBase
{
    [HttpPost]
    public async Task<IActionResult> PostCommand(Guid deviceId)
    {
        return Ok();
    }

    
}