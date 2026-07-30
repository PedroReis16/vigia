using Vigia.Models.Enums;

namespace Vigia.Models.Entities;

public class Device : BaseEntity
{
    public string Name { get; set; } = null!;
    public string? Nickname { get; set; }
    public string MacAddress { get; set; } = null!;
    public DeviceRooms? Room { get; set; }

    public Group? Group { get; set; } = null;   // Group != null -> Dispositivo vinculado a um grupo de usuários
}