using Vigia.Models.Enums;

namespace Vigia.Models.Entities;

public class Device : BaseEntity
{
    public string Name { get; set; } = null!;
    public string? Nickname { get; set; }
    public string MacAddress { get; set; } = null!;
    public DeviceRooms? Room { get; set; }
    /// <summary>Ed25519 public key (raw 32 bytes as hex).</summary>
    public string SignPublicKey { get; set; } = null!;

    public Group? Group { get; set; } = null;   // Group != null -> Dispositivo vinculado a um grupo de usuários
}