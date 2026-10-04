using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts.Clips;
using Vigia.API.Models.DTOs.Devices;
using Vigia.API.Services.Clips;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[AllowAnonymous]
[Route("devices/{deviceId}/clips")]
public class DevicesClipController(IClipIngestService clips) : ControllerBase
{
    private readonly IClipIngestService _clips = clips;

    /// <summary>
    /// Abre uma sessão para receber os frames numerados de um clipe.
    /// </summary>
    [HttpPost]
    [Consumes("application/json")]
    [ProducesResponseType(StatusCodes.Status202Accepted)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> OpenSession(Guid deviceId, [FromBody] OpenClipSessionDTO session, CancellationToken cancellationToken)
    {
        await _clips.OpenSessionAsync(deviceId, session, cancellationToken);
        return Accepted();
    }

    /// <summary>
    /// Recebe um frame PNG já decodificável, gravado pelo índice na sequência.
    /// </summary>
    [HttpPost("{clipId}/frames/{index:int}")]
    [Consumes("image/png")]
    [RequestSizeLimit(ClipIngestService.MaxPngBytes)]
    [ProducesResponseType(StatusCodes.Status202Accepted)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> PostFrame(Guid deviceId, Guid clipId, int index, CancellationToken cancellationToken)
    {
        await _clips.SaveFrameAsync(deviceId, clipId, index, Request.Body, cancellationToken);
        return Accepted();
    }

    /// <summary>
    /// Lista os clipes do dispositivo.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(List<DeviceClipDTO>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> List(Guid deviceId, CancellationToken cancellationToken)
    {
        List<DeviceClipDTO> clips = await _clips.ListAsync(deviceId, cancellationToken);
        return Ok(clips);
    }

    /// <summary>
    /// Devolve o MP4 do clipe quando a montagem terminou.
    /// </summary>
    [HttpGet("{clipId}")]
    [ProducesResponseType(typeof(FileResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetVideo(Guid deviceId, Guid clipId, CancellationToken cancellationToken)
    {
        Stream? video = await _clips.OpenVideoAsync(deviceId, clipId, cancellationToken);
        if (video == null)
            return NotFound();

        return File(video, "video/mp4");
    }
}
