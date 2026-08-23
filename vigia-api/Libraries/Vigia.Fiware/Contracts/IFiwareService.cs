using Vigia.Fiware.Models.DeviceDTOs;
using Vigia.Models.Enums;

namespace Vigia.Fiware.Contracts;

public interface IFiwareService
{
    /// <summary>
    /// Verifica se o serviço do FIWARE está disponível conforme as configurações definidas nas configurações do projeto.
    /// Quando o serviço não esta dísponível ou as configurações divergem dos valores definidos, o serviço é registrado ou atualizado
    /// </summary>
    Task<bool> AddOrUpdateServiceAsync();

    /// <summary>
    /// Compara o schema de <c>Fiware:Devices</c> com o último valor persistido em
    /// <c>FiwareProperties</c>. Se houver divergência, atualiza os devices no IoT Agent
    /// via PUT e persiste o novo schema no banco.
    /// </summary>
    Task<bool> SyncDevicesSchemaAsync();

    /// <summary>
    /// Garante as subscrições Orion definidas em <c>Fiware:Subscriptions</c>
    /// para todos os devices do IoT Agent. Idempotente: reaproveita a subscrição
    /// correta e remove duplicatas da mesma URL.
    /// </summary>
    Task<bool> SyncSubscriptionsAsync();

    /// <summary>
    /// Provisiona um device no IoT Agent com o schema canônico de
    /// <c>Fiware:Devices</c>, sincroniza a registration de comandos no Orion
    /// e as subscrições de <c>Fiware:Subscriptions</c>. Idempotente: se o device
    /// já existir, apenas reforça registration/subscrições.
    /// </summary>
    Task<bool> RegisterSensorAsync(Guid deviceId, string deviceName);

    /// <summary>
    /// Garante que cada device da lista esteja provisionado no IoT Agent.
    /// Usado no startup para reconciliar órfãos (existem no Postgres, ausentes no FIWARE).
    /// </summary>
    Task<bool> EnsureDevicesProvisionedAsync(IReadOnlyCollection<(Guid DeviceId, string DeviceName)> devices);

#if DEBUG
    /// <summary>
    /// Garante que o dispositivo de teste (<c>TestDeviceSeed</c>) esteja provisionado
    /// no IoT Agent, com registration de comandos e subscrições do Orion. Idempotente.
    /// </summary>
    Task<bool> EnsureSeedDeviceAsync();
#endif

    Task DeleteSensorAsync(Guid id, string name);
    Task<bool> SendCommandAsync(string deviceName, DeviceCommands command, string? commandValue = null);

    /// <summary>
    /// Lista uma página de devices provisionados no IoT Agent.
    /// </summary>
    Task<(List<IotAgentDeviceDTO> Devices, int TotalCount)> ListDevicesPageAsync(int offset, int limit);
}
