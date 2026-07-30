using Vigia.Models.Enums;

namespace Vigia.API.Models.DTOs.Devices;

public class DeviceDTO
{
    public Guid Id { get; set; }
    public string Nickname { get; set; } = string.Empty;
    public string MacAddress { get; set; } = string.Empty;
    public DeviceRooms? Room { get; set; }
    public Guid? OwnerId { get; set; }
}