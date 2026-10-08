using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts.Clips;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Devices;
using Vigia.API.Services.Clips;
using Vigia.Cloud.Contracts;
using Vigia.Models.Middlewares;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/{deviceId}/clips")]
public class DevicesClipController(IClipIngestService clips) : ControllerBase
{
    private readonly IClipIngestService _clips = clips;

    /// <summary>
    /// Abre uma sessão para receber os frames numerados de um clipe.
    /// A placa envia sem token de usuário.
    /// </summary>
    [HttpPost]
    [AllowAnonymous]
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
    /// A placa envia sem token de usuário.
    /// </summary>
    [HttpPost("{clipId}/frames/{index:int}")]
    [AllowAnonymous]
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
    /// Lista os clipes do dispositivo. Clip pronto inclui URLs de thumbnail e playback com token efêmero.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(List<DeviceClipDTO>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> List(Guid deviceId, CancellationToken cancellationToken)
    {
        List<DeviceClipDTO> clips = await _clips.ListAsync(deviceId, User.GetUserId(), cancellationToken);
        return Ok(clips);
    }

    /// <summary>
    /// JPEG do momento da queda. O acesso usa o token efêmero emitido em thumbnailUrl.
    /// </summary>
    [HttpGet("{clipId}/thumbnail")]
    [Authorize(AuthenticationSchemes = ClipAccessTokenDefaults.AuthenticationScheme)]
    [ProducesResponseType(typeof(FileResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> GetThumbnail(Guid deviceId, Guid clipId, CancellationToken cancellationToken)
    {
        Stream? image = await _clips.OpenThumbnailAsync(deviceId, clipId, cancellationToken);
        if (image == null)
            return NotFound();

        return File(image, "image/jpeg");
    }

    /// <summary>
    /// Transmite o MP4 por faixas HTTP. O acesso usa o token efêmero emitido em playbackUrl.
    /// </summary>
    [HttpGet("{clipId}")]
    [Authorize(AuthenticationSchemes = ClipAccessTokenDefaults.AuthenticationScheme)]
    [ProducesResponseType(typeof(FileResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status206PartialContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status416RangeNotSatisfiable)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> GetVideo(Guid deviceId, Guid clipId, CancellationToken cancellationToken)
    {
        long? total = await _clips.GetVideoLengthAsync(deviceId, clipId, cancellationToken);
        if (total == null)
            return NotFound();

        if (ClipByteRanges.TryResolve(Request.Headers.Range.ToString(), total.Value, out ClipByteRange range, out bool unsatisfiable))
        {
            CloudObjectRead? slice = await _clips.OpenVideoAsync(deviceId, clipId, range.Start, range.End, cancellationToken);
            if (slice == null)
                return NotFound();

            return new ClipByteRangeResult(slice, "video/mp4", partial: true);
        }

        if (unsatisfiable)
        {
            Response.Headers.ContentRange = $"bytes */{total.Value}";
            return StatusCode(StatusCodes.Status416RangeNotSatisfiable);
        }

        CloudObjectRead? video = await _clips.OpenVideoAsync(deviceId, clipId, null, null, cancellationToken);
        if (video == null)
            return NotFound();

        return new ClipByteRangeResult(video, "video/mp4", partial: false);
    }
}
