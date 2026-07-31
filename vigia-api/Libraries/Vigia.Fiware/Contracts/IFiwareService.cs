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
    /// Provisiona um novo device no IoT Agent já com o schema canônico de
    /// <c>Fiware:Devices</c> e sincroniza a registration de comandos no Orion.
    /// </summary>
    Task<bool> RegisterSensorAsync(Guid deviceId, string deviceName);

#if DEBUG
    /// <summary>
    /// Garante que o dispositivo de teste (<c>TestDeviceSeed</c>) esteja provisionado
    /// no IoT Agent e com registration de comandos no Orion. Idempotente.
    /// </summary>
    Task<bool> EnsureSeedDeviceAsync();
#endif

    Task DeleteSensorAsync(Guid id, string name);
}
