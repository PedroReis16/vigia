using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Models.Seed;

/// <summary>
/// Fachada do device mock primário (slot 0 do <see cref="MockDevicesSeed"/>).
/// Mantida para compatibilidade com seed-codes, edge local e testes existentes.
/// </summary>
public static class TestDeviceSeed
{
    public static readonly Guid Id = MockDevicesSeed.Primary.Id;
    public const string Name = "Vigia-a1b2c3d4";
    public const string Nickname = "Câmera Teste";
    public const string MacAddress = "AA:BB:CC:DD:EE:FF";

    public static readonly DeviceRooms Room = DeviceRooms.LivingRoom;

    /// <summary>Grupo do Admin (<c>GroupsConfiguration</c>).</summary>
    public static readonly Guid GroupId = MockDevicesSeed.GroupId;

    /// <summary>Mesmo UUID do usuário <c>admin</c> do realm Keycloak <c>vigia</c>.</summary>
    public static readonly Guid OwnerId = MockDevicesSeed.OwnerId;
    public const string OwnerEmail = MockDevicesSeed.OwnerEmail;
    public const string OwnerPhone = MockDevicesSeed.OwnerPhone;

    public static readonly DateTime CreatedAt = MockDevicesSeed.CreatedAt;

    public static Device Create() => MockDevicesSeed.Create(MockDevicesSeed.Primary);
}
