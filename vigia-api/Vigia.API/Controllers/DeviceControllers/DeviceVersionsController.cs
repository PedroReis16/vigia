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


    [HttpGet]
    public async Task<IActionResult> GetDeviceVersions()
    {
        return Ok();
    }

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

        await using var stream = new FileStream(filePath, FileMode.Append, FileAccess.Write, FileShare.None);
        await fileChunk.CopyToAsync(stream);

        if (chunkIndex == totalChunks - 1)
        {
            await _service.UploadDeviceVersionAsync(version, filePath);
            return Ok(new { message = "Versão do dispositivo atualizada com sucesso" });
        }

        return Ok(new { message = $"Chunk {chunkIndex + 1}/{totalChunks} enviado com sucesso." });
    }
}