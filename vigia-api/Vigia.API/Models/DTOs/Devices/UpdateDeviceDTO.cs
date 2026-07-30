using Vigia.Models.Enums;

namespace Vigia.API.Models.DTOs.Devices;

public class UpdateDeviceDTO
{
    public string? Nickname { get; set; }
    public DeviceRooms? Room { get; set; }
}