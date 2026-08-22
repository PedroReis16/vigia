using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Config;
using Vigia.API.Contracts.Devices;

namespace Vigia.API.Controllers.DeviceControllers;

/// <summary>
/// Pacote OTA rolling do onboard (um artefato sobrescrito; sem histórico SemVer).
/// </summary>
[ApiController]
[Route("devices/updates")]
public class DeviceUpdatesController(IVersionService service, IConfiguration configuration) : ControllerBase
{
    private readonly IVersionService _service = service;
    private readonly string _stagingFolder = Path.Combine(
        Directory.GetCurrentDirectory(),
        configuration.GetValue<string>(AppSettingsProperties.VersionPath)!);

    /// <summary>
    /// Metadados do pacote rolling atual (<c>revision</c> para o device comparar com o instalado).
    /// </summary>
    [HttpGet("current")]
    [AllowAnonymous]
    public async Task<IActionResult> GetCurrentUpdate()
    {
        DeviceUpdateInfo? info = await _service.GetCurrentUpdateAsync();
        if (info is null)
            return NotFound(new { message = "Nenhum pacote OTA disponível" });

        return Ok(new { revision = info.Revision, available = info.Available });
    }

    /// <summary>
    /// Stream do pacote OTA rolling atual.
    /// </summary>
    [HttpGet("download")]
    [AllowAnonymous]
    public async Task<IActionResult> DownloadCurrentUpdate()
    {
        Stream stream = await _service.DownloadCurrentUpdateAsync();
        return File(stream, "application/gzip", "vigia-fall-ota-onboard.tar.gz");
    }

    /// <summary>
    /// Upload chunked. No último chunk: sobrescreve o pacote rolling e notifica via FIWARE.
    /// Form: fileChunk, fileId, chunkIndex, totalChunks, revision (ex.: git SHA).
    /// </summary>
    [HttpPost]
    [AllowAnonymous]
    public async Task<IActionResult> UploadDeviceUpdate(
        [FromForm] IFormFile fileChunk,
        [FromForm] string revision,
        [FromForm] Guid fileId,
        [FromForm] int chunkIndex,
        [FromForm] int totalChunks
    )
    {
        if (fileChunk is null || fileChunk.Length == 0)
            return BadRequest("File chunk is required");

        if (string.IsNullOrWhiteSpace(revision))
            return BadRequest("revision is required");

        Directory.CreateDirectory(_stagingFolder);
        string filePath = Path.Combine(_stagingFolder, fileId.ToString());

        await using (var stream = new FileStream(filePath, FileMode.Append, FileAccess.Write, FileShare.None))
        {
            await fileChunk.CopyToAsync(stream);
        }

        if (chunkIndex == totalChunks - 1)
        {
            await _service.UploadDeviceUpdateAsync(revision.Trim(), filePath);
            return Ok(new { message = "Pacote OTA atualizado com sucesso" });
        }

        return Ok(new { message = $"Chunk {chunkIndex + 1}/{totalChunks} enviado com sucesso." });
    }
}
