using Microsoft.AspNetCore.Mvc;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("devices/versions")]
public class DeviceVersionsController : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetDeviceVersions()
    {
        return Ok();
    }

    [HttpPost]
    public async Task<IActionResult> UploadDeviceVersion(
        [FromForm] IFormFile fileChunk,
        [FromForm] Guid fileId,
        [FromForm] int chunkIndex,
        [FromForm] int totalChunks
    )
    {
        if (fileChunk is null || fileChunk.Length == 0)
            return BadRequest("File chunk is required");

        using var stream = new FileStream("", FileMode.Append, FileAccess.Write, FileShare.None);
        await fileChunk.CopyToAsync(stream);


        if (chunkIndex == totalChunks - 1)
        {
             
        }

        return Ok(new { message = $"Chunk {chunkIndex + 1}/{totalChunks} enviado com sucesso." });
    }
}