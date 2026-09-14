using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Alerts;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/alert")]
public class AlertController(IAlertService service) : ControllerBase
{
    private readonly IAlertService _service = service;

    /// <summary>
    /// Webhook do Orion: recebe notificação quando <c>fall_state</c> passa a <c>fall</c>.
    /// </summary>
    [HttpPost]
    [AllowAnonymous]
    [Consumes("application/json")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> CreateDeviceAlert([FromBody] OrionAlertNotificationDTO notification)
    {
        await _service.HandleFallWebhookAsync(notification);
        return Ok();
    }
}
