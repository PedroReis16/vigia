using Vigia.Fiware.Models.DeviceDTOs;

namespace Vigia.Fiware.Config;

public static class DeviceProperties
{
    internal const string Protocol = "PDI-IoTA-UltraLight";
    internal const string Transport = "MQTT";

    internal static readonly ICollection<DeviceCommandDTO> CameraCommands = [];

    internal static readonly ICollection<DeviceAttributeDTO> CameraAttributes = [];

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
