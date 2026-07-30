namespace Vigia.Fiware.Contracts;

public interface IFiwareService
{
    /// <summary>
    /// Verifica se o serviço do FIWARE está disponível conforme as configurações definidas nas configurações do projeto.
    /// Quando o serviço não esta dísponível ou as configurações divergem dos valores definidos, o serviço é registrado ou atualizado
    /// </summary>
    /// <returns></returns>
    Task<bool> AddOrUpdateServiceAsync();
}