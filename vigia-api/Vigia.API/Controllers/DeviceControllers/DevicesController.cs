using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Models.Enums;

namespace Vigia.API.Controllers.DeviceControllers;

[ApiController]
[Route("[controller]")]
[Authorize]
public class DevicesController(IDevicesService service) : ControllerBase
{
    private readonly IDevicesService _service = service;

    /// <summary>
    /// Registra um novo dispositivo no sistema, captando informações de identificação do hardware
    /// </summary>
    /// <returns></returns>
    [HttpPost("register")]
    public async Task<IActionResult> RegisterDevice([FromBody] NewDeviceDTO newDevice)
    {
        await _service.RegisterDeviceAsync(newDevice);

        return Created();
    }

    ///<summary>
    /// Detalhes de um dispositivo
    /// </summary>
    /// <param name="deviceId"></param>
    /// <returns></returns>
    [HttpGet("{deviceId}")]
    public async Task<IActionResult> GetDevice(Guid deviceId)
    {
        DeviceDTO? device = await _service.GetDeviceAsync(deviceId);
        if (device == null)
            return NoContent();

        return Ok(device);
    }

    /// <summary>
    /// Lista todos os dispositivos registrados no sistema
    /// </summary>
    /// <param name="nickname">Nome do dispositivo</param>
    /// <param name="room">Ambiente do dispositivo</param>
    /// <param name="onlyShared">Somente dispositivos compartilhados pelo usuários</param>
    /// <param name="onlyOwned">Somente dispositivos pertencentes ao usuário</param>
    /// <param name="page">Número da página</param>
    /// <param name="pageSize">Quantidade de dispositivos por página</param>
    /// <returns></returns>
    [HttpGet("list")]
    public async Task<IActionResult> ListDevices(
        [FromQuery] string? nickname = null,
        [FromQuery] DeviceRooms? room = null,
        [FromQuery] bool onlyShared = false,
        [FromQuery] bool onlyOwned = false,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10
        )
    {
        Guid userId = User.GetUserId();

        List<DeviceDTO> devices = await _service.ListDevicesAsync(userId, nickname, room, onlyShared, onlyOwned, page, pageSize);

        return Ok(devices);
    }

    /// <summary>
    /// Atualiza as informações de um dispositivo registrado no sistema
    /// </summary>
    /// <param name="deviceId">O ID do dispositivo a ser atualizado</param>
    /// <param name="updatedDevice">As novas informações do dispositivo</param>
    /// <returns></returns>
    [HttpPut("{deviceId}")]
    public async Task<IActionResult> UpdateDevice(Guid deviceId, [FromBody] UpdateDeviceDTO updatedDevice)
    {
        try
        {
            Guid userId = User.GetUserId();

            await _service.UpdateDeviceAsync(userId, deviceId, updatedDevice);
            return Ok(new { message = "Dispositivo atualizado com sucesso" });
        }
        catch (UnauthorizedAccessException) { return Forbid(); }
        catch (Exception) { throw; }

    }
}