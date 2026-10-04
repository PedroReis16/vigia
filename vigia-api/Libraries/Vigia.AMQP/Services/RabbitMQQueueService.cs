using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Vigia.AMQP.Configuration;
using Vigia.AMQP.Contracts;
using RabbitMQ.Client;

namespace Vigia.AMQP.Services;

public abstract class RabbitMQQueueService : IQueueService
{
    protected readonly ILogger<RabbitMQQueueService> Logger;
    protected readonly RabbitMQConfiguration Configuration;
    protected IConnection? Connection;
    protected IModel? Channel;

    protected RabbitMQQueueService(ILogger<RabbitMQQueueService> logger, IConfiguration configuration)
    {

        Logger = logger;

        IConfigurationSection section = configuration.GetRequiredSection("RabbitMQ");
        Configuration = BindRabbitMQConfiguration(section);
    }

    /// <summary>
    /// Lê a seção RabbitMQ de forma explícita para garantir Port e demais valores em qualquer
    /// provedor de configuração (appsettings, in-memory em testes, variáveis de ambiente).
    /// </summary>
    private static RabbitMQConfiguration BindRabbitMQConfiguration(IConfigurationSection section)
    {
        string hostName = section["HostName"] ?? section["hostname"] ?? "localhost";
        string portStr = section["Port"] ?? section["port"] ?? "5672";
        int port = int.TryParse(portStr, out int p) ? p : 5672;
        string username = section["Username"] ?? section["username"] ?? "guest";
        string password = section["Password"] ?? section["password"] ?? "guest";

        return new RabbitMQConfiguration
        {
            HostName = hostName,
            Port = port,
            Username = username,
            Password = password
        };
    }

    /// <summary>
    /// Garante que Connection e Channel existam; chamado na primeira utilização (lazy init)
    /// para permitir testes unitários que instanciam o serviço sem conectar ao broker.
    /// </summary>
    protected void EnsureConnection()
    {
        if (Connection is null)
            Initialize();
    }

    public virtual void Initialize()
    {
        try
        {
            if (Connection is null)
            {
                Logger.LogDebug("Inicializando conexão com o RabbitMQ");
                ConnectionFactory factory = new()
                {
                    HostName = Configuration.HostName,
                    Port = Configuration.Port,
                    UserName = Configuration.Username,
                    Password = Configuration.Password,
                    // Obrigatório para AsyncEventingBasicConsumer: sem isso, handlers async que fazem await
                    // bloqueiam o thread de dispatch e as mensagens permanecem em unacked indefinidamente.
                    DispatchConsumersAsync = true
                };
                Connection = factory.CreateConnection();
            }

            if (Channel is null)
            {
                Channel = Connection.CreateModel();
                Logger.LogDebug("Inicializando canal com o RabbitMQ");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError(ex, "Erro durante a inicialização do RabbitMQ: {ErrorMessage}", ex.Message);
            throw;
        }
    }

    public void Dispose()
    {
        Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!disposing)
            return;

        // Fechar o canal antes da conexão para evitar NullReferenceException no AutorecoveringModel.Abort()
        // quando a conexão é fechada primeiro e o canal fica em estado inválido.
#pragma warning disable CA1031 // Intentional: ignore teardown errors from invalid AutorecoveringModel state
        try
        {
            if (Channel != null)
            {
                Channel.Dispose();
                Channel = null;
            }
        }
        catch (Exception)
        {
            // Ignora erros no teardown (ex.: AutorecoveringModel.Abort() com estado inválido)
        }

        try
        {
            Connection?.Dispose();
            Connection = null;
        }
        catch (Exception)
        {
            // Ignora erros no teardown
        }
#pragma warning restore CA1031
    }
}