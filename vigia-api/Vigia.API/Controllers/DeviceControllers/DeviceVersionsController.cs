using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Config;
using Vigia.API.Contracts.Devices;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/versions")]
public class DeviceVersionsController(IVersionService service, IConfiguration configuration) : ControllerBase
{
    private readonly IVersionService _service = service;
    private readonly string _versionFolder = Path.Combine(Directory.GetCurrentDirectory(), configuration.GetValue<string>(AppSettingsProperties.VersionPath)!);

    /// <summary>
    /// Lista as versões disponíveis no bucket de artefatos OTA.
    /// </summary>
    [HttpGet]
    [AllowAnonymous]
    public async Task<IActionResult> GetDeviceVersions()
    {
        IReadOnlyList<string> versions = await _service.ListVersionsAsync();
        return Ok(versions);
    }

    /// <summary>
    /// Retorna a maior versão SemVer disponível (pré-releases ignoradas se houver estável).
    /// </summary>
    [HttpGet("latest")]
    [AllowAnonymous]
    public async Task<IActionResult> GetLatestDeviceVersion()
    {
        string? latest = await _service.GetLatestVersionAsync();
        if (latest is null)
            return NotFound(new { message = "Nenhuma versão disponível" });

        return Ok(new { version = latest });
    }

    /// <summary>
    /// Faz stream do pacote OTA da versão solicitada a partir do S3/MinIO.
    /// </summary>
    [HttpGet("{version}/download")]
    [AllowAnonymous]
    public async Task<IActionResult> DownloadDeviceVersion(string version)
    {
        Stream stream = await _service.DownloadVersionAsync(version);
        return File(stream, "application/gzip", $"{version}.tar.gz");
    }

    /// <summary>
    /// Upload chunked de uma nova versão. No último chunk: grava no bucket e notifica devices via FIWARE.
    /// </summary>
    [HttpPost]
    [AllowAnonymous]
    public async Task<IActionResult> UploadDeviceVersion(
        [FromForm] IFormFile fileChunk,
        [FromForm] string version,
        [FromForm] Guid fileId,
        [FromForm] int chunkIndex,
        [FromForm] int totalChunks
    )
    {
        if (fileChunk is null || fileChunk.Length == 0)
            return BadRequest("File chunk is required");

        Directory.CreateDirectory(_versionFolder);
        string filePath = Path.Combine(_versionFolder, fileId.ToString());

        await using (var stream = new FileStream(filePath, FileMode.Append, FileAccess.Write, FileShare.None))
        {
            await fileChunk.CopyToAsync(stream);
        }

        if (chunkIndex == totalChunks - 1)
        {
            await _service.UploadDeviceVersionAsync(version, filePath);
            return Ok(new { message = "Versão do dispositivo atualizada com sucesso" });
        }

        return Ok(new { message = $"Chunk {chunkIndex + 1}/{totalChunks} enviado com sucesso." });
    }
}
