namespace Vigia.Fiware.Contracts;

public interface IFiwareService
{
    /// <summary>
    /// Verifica se o serviço do FIWARE está disponível conforme as configurações definidas nas configurações do projeto.
    /// Quando o serviço não esta dísponível ou as configurações divergem dos valores definidos, o serviço é registrado ou atualizado
    /// </summary>
    Task<bool> AddOrUpdateServiceAsync();

    /// <summary>
    /// Sincroniza attributes/commands de todos os devices provisionados no IoT Agent
    /// com os valores definidos em <c>Fiware:Devices</c> (appsettings), e garante
    /// que as registrations de comandos no Orion estejam alinhadas.
    /// </summary>
    Task<bool> SyncDevicesSchemaAsync();

    /// <summary>
    /// Provisiona um novo device no IoT Agent já com o schema canônico de
    /// <c>Fiware:Devices</c> e sincroniza a registration de comandos no Orion.
    /// </summary>
    Task<bool> RegisterSensorAsync(Guid deviceId, string deviceName);
    Task DeleteSensorAsync(Guid id, string name);
}
