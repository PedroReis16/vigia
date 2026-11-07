using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Models.Seed;

/// <summary>
/// Pool exclusivo do worker <c>vigia-devices</c> (DEBUG). Todos no grupo do admin.
/// Não inclui <see cref="TestDeviceSeed"/> (edge real / seed-codes).
/// Espelhar IDs em <c>vigia-devices/device_pool.json</c> ao alterar.
/// </summary>
public static class MockDevicesSeed
{
    /// <summary>Grupo do Admin — mesmo de <see cref="TestDeviceSeed.GroupId"/>.</summary>
    public static readonly Guid GroupId = TestDeviceSeed.GroupId;

    public static readonly DateTime CreatedAt = TestDeviceSeed.CreatedAt;

    /// <summary>
    /// Devices só para o worker mock. Nunca reutilizar o ID de
    /// <see cref="TestDeviceSeed"/> nem de placas reais.
    /// </summary>
    public static IReadOnlyList<MockDeviceDefinition> All { get; } =
    [
        new(
            Id: new Guid("a1b2c3d4-e5f6-4789-a012-3456789abcde"),
            Name: "Vigia-e5f67890",
            Nickname: "Sala TV",
            MacAddress: "AA:BB:CC:DD:EE:01",
            Room: DeviceRooms.LivingRoom),
        new(
            Id: new Guid("b2c3d4e5-f6a7-4890-b123-456789abcdef"),
            Name: "Vigia-f6a78901",
            Nickname: "Quarto Casal",
            MacAddress: "AA:BB:CC:DD:EE:02",
            Room: DeviceRooms.Bedroom),
        new(
            Id: new Guid("c3d4e5f6-a7b8-4901-c234-56789abcdef0"),
            Name: "Vigia-a7b89012",
            Nickname: "Cozinha",
            MacAddress: "AA:BB:CC:DD:EE:03",
            Room: DeviceRooms.Kitchen),
        new(
            Id: new Guid("d4e5f6a7-b8c9-4012-d345-6789abcdef01"),
            Name: "Vigia-b8c90123",
            Nickname: "Escritório",
            MacAddress: "AA:BB:CC:DD:EE:04",
            Room: DeviceRooms.Office),
        new(
            Id: new Guid("e5f6a7b8-c9d0-4123-e456-789abcdef012"),
            Name: "Vigia-c9d01234",
            Nickname: "Banheiro",
            MacAddress: "AA:BB:CC:DD:EE:05",
            Room: DeviceRooms.Bathroom),
        new(
            Id: new Guid("f6a7b8c9-d0e1-4234-f567-89abcdef0123"),
            Name: "Vigia-d0e12345",
            Nickname: "Garagem",
            MacAddress: "AA:BB:CC:DD:EE:06",
            Room: DeviceRooms.Garage),
        new(
            Id: new Guid("07b8c9d0-e1f2-4345-a678-9abcdef01234"),
            Name: "Vigia-e1f23456",
            Nickname: "Quintal",
            MacAddress: "AA:BB:CC:DD:EE:07",
            Room: DeviceRooms.Backyard),
    ];

    public static Device Create(MockDeviceDefinition definition) => new()
    {
        Id = definition.Id,
        Name = definition.Name,
        Nickname = definition.Nickname,
        MacAddress = definition.MacAddress,
        Room = definition.Room,
        GroupId = GroupId,
        CreatedAt = CreatedAt,
        UpdatedAt = null,
        DeletedAt = null,
    };

    public static IEnumerable<(Guid DeviceId, string DeviceName)> AsProvisionPairs() =>
        All.Select(d => (d.Id, d.Name));
}

/// <summary>Definição imutável de um device do pool mock.</summary>
public sealed record MockDeviceDefinition(
    Guid Id,
    string Name,
    string Nickname,
    string MacAddress,
    DeviceRooms Room);
