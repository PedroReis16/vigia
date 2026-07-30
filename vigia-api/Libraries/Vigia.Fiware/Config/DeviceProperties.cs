using Vigia.Fiware.Models.DeviceDTOs;

namespace Vigia.Fiware.Config;

public static class DeviceProperties
{
    internal const string Protocol = "PDI-IoTA-UltraLight";
    internal const string Transport = "MQTT";

    private static readonly ICollection<DeviceCommandDTO> CameraCommands = [
        new DeviceCommandDTO { Name = DeviceCommands.StreamOn, Type = "command" },
        new DeviceCommandDTO { Name = DeviceCommands.StreamOff, Type = "command" },
        new DeviceCommandDTO { Name = DeviceCommands.DeviceOn, Type = "command" },
        new DeviceCommandDTO { Name = DeviceCommands.DeviceOff, Type = "command" },
    ];

    // object_id = alias curto usado no protocolo Ultralight; name = atributo NGSI no Orion
    private static readonly ICollection<DeviceAttributeDTO> CameraAttributes = [
        new DeviceAttributeDTO { ObjectId = "s", Name = DeviceAttributes.Status, Type = "Text" },
        new DeviceAttributeDTO { ObjectId = "ns", Name = DeviceAttributes.NetworkStatus, Type = "Text" },
        new DeviceAttributeDTO { ObjectId = "ss", Name = DeviceAttributes.StreamStatus, Type = "Text" },
        new DeviceAttributeDTO { ObjectId = "dp", Name = DeviceAttributes.DetectedPerson, Type = "Boolean" },
        new DeviceAttributeDTO { ObjectId = "df", Name = DeviceAttributes.DetectedFall, Type = "Boolean" },
    ];

    internal static List<DeviceCommandDTO> GetCameraCommands() =>
        CameraCommands.Select(c => new DeviceCommandDTO { Name = c.Name, Type = c.Type }).ToList();

    internal static List<DeviceAttributeDTO> GetCameraAttributes() =>
        CameraAttributes.Select(a => new DeviceAttributeDTO
        {
            ObjectId = a.ObjectId,
            Name = a.Name,
            Type = a.Type
        }).ToList();

    internal static string BuildEntityName(string entityType, Guid deviceId) =>
        $"urn:ngsi-ld:{entityType}:{deviceId}";
}
