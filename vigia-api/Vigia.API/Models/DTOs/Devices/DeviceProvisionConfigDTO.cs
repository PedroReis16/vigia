namespace Vigia.API.Models.DTOs.Devices;

/// <summary>
/// Configuração enviada ao app durante o pareamento, para provisionar o dispositivo
/// (Wi‑Fi + integrações). Novos campos podem ser adicionados aqui sem alterar o contrato de registro/vínculo.
/// </summary>
public class DeviceProvisionConfigDTO
{
    public string FiwareApiKey { get; set; } = string.Empty;
    public string StreamIngestUrl { get; set; } = string.Empty;
}
