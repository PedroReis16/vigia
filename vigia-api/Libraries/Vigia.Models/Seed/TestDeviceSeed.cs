using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Models.Seed;

/// <summary>
/// Dispositivo de teste usado apenas em builds DEBUG (seed no banco + provisionamento FIWARE).
/// </summary>
public static class TestDeviceSeed
{
    public static readonly Guid Id = new("b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c");
    public const string Name = "Vigia-a1b2c3d4";
    public const string Nickname = "Câmera Teste";
    public const string MacAddress = "AA:BB:CC:DD:EE:FF";

    /// <summary>
    /// Ed25519 raw public key (hex). Private seed for local DEBUG scripts is derived as
    /// SHA-256 UTF-8 of <c>vigia-debug-test-device-v1</c> (see <c>seed-codes/publish_frame.py</c>
    /// and <c>vigia-fall/shared/test_device_seed.py</c>) — never commit the raw private hex.
    /// </summary>
    public const string SignPublicKey = "10ef4349806050a8e17a82781f188165b70cd19d176c70ec5154c6d9ede4b59d";

    public static readonly DeviceRooms Room = DeviceRooms.LivingRoom;

    /// <summary>Grupo do Admin (<c>GroupsConfiguration</c>).</summary>
    public static readonly Guid GroupId = new("80eed123-8e77-47a3-8fae-cedb1ab3eef7");

    public static readonly DateTime CreatedAt =
        new DateTime(2026, 7, 27, 17, 42, 22, 525, DateTimeKind.Utc).AddTicks(2940);

    public static Device Create() => new()
    {
        Id = Id,
        Name = Name,
        Nickname = Nickname,
        MacAddress = MacAddress,
        Room = Room,
        SignPublicKey = SignPublicKey,
        GroupId = GroupId,
        CreatedAt = CreatedAt,
        UpdatedAt = null,
        DeletedAt = null
    };
}
