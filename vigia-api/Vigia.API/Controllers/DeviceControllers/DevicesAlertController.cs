using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Authorize]
[Route("devices")]
public class DevicesAlertController(INotificationInboxService service) : ControllerBase
{
    private readonly INotificationInboxService _service = service;

    /// <summary>
    /// Confirma acesso ao device após alerta de queda: para reenvios e marca lidas do usuário.
    /// </summary>
    [HttpPost("{deviceId:guid}/alerts/acknowledge")]
    public async Task<IActionResult> Acknowledge(Guid deviceId)
    {
        await _service.AcknowledgeDeviceAlertsAsync(User.GetUserId(), deviceId);
        return NoContent();
    }
}
