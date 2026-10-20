using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Notifications;

namespace Vigia.API.Controllers;

[ApiController]
[Authorize]
[Route("notifications")]
public class NotificationsController(INotificationInboxService service) : ControllerBase
{
    private readonly INotificationInboxService _service = service;

    /// <summary>
    /// Lista o inbox de notificações do usuário autenticado.
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<NotificationListDTO>> List(
        [FromQuery] int? skip = null,
        [FromQuery] int? take = null)
    {
        NotificationListDTO result = await _service.ListAsync(User.GetUserId(), skip, take);
        return Ok(result);
    }

    /// <summary>
    /// Marca uma notificação como lida.
    /// </summary>
    [HttpPost("{notificationId:guid}/read")]
    public async Task<IActionResult> MarkRead(Guid notificationId)
    {
        await _service.MarkReadAsync(User.GetUserId(), notificationId);
        return NoContent();
    }

    /// <summary>
    /// Marca todas as notificações do usuário como lidas.
    /// </summary>
    [HttpPost("read-all")]
    public async Task<IActionResult> MarkAllRead()
    {
        await _service.MarkAllReadAsync(User.GetUserId());
        return NoContent();
    }
}
