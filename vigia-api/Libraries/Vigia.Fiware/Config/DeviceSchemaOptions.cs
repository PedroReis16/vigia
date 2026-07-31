using Vigia.Fiware.Models.DeviceDTOs;

namespace Vigia.Fiware.Config;

/// <summary>
/// Schema de devices FIWARE, carregado de <c>Fiware:Devices</c> no appsettings.
/// </summary>
public class DeviceSchemaOptions
{
    public const string SectionName = "Fiware:Devices";

    public string Protocol { get; set; } = "PDI-IoTA-UltraLight";

    public string Transport { get; set; } = "MQTT";

    public List<DeviceCommandDTO> Commands { get; set; } = [];

    public List<DeviceAttributeDTO> Attributes { get; set; } = [];

    public List<DeviceCommandDTO> GetCommands() =>
        Commands
            .Where(c => !string.IsNullOrWhiteSpace(c.Name))
            .GroupBy(c => $"{c.Name}|{c.Type}", StringComparer.Ordinal)
            .Select(group => new DeviceCommandDTO
            {
                Name = group.First().Name,
                Type = group.First().Type
            })
            .ToList();

    public List<DeviceAttributeDTO> GetAttributes() =>
        Attributes
            .Where(a => !string.IsNullOrWhiteSpace(a.Name) && !string.IsNullOrWhiteSpace(a.ObjectId))
            .GroupBy(a => $"{a.ObjectId}|{a.Name}|{a.Type}", StringComparer.Ordinal)
            .Select(group => new DeviceAttributeDTO
            {
                ObjectId = group.First().ObjectId,
                Name = group.First().Name,
                Type = group.First().Type
            })
            .ToList();
}
