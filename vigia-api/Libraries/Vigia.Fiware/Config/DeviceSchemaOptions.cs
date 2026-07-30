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
        Commands.Select(c => new DeviceCommandDTO { Name = c.Name, Type = c.Type }).ToList();

    public List<DeviceAttributeDTO> GetAttributes() =>
        Attributes.Select(a => new DeviceAttributeDTO
        {
            ObjectId = a.ObjectId,
            Name = a.Name,
            Type = a.Type
        }).ToList();
}
