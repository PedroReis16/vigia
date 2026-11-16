using System.Collections.Concurrent;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Vigia.AMQP.Contracts;
using RabbitMQ.Client;

namespace Vigia.AMQP.Services;

public class RabbitMQPublisherService(ILogger<RabbitMQPublisherService> logger, IConfiguration configuration) : RabbitMQQueueService(logger, configuration), IPublisherService
{
    private readonly ConcurrentQueue<ExchangeConfig> _pendingExchangeConfigs = new();
    private bool _exchangeConfigsApplied;

    /// <summary>
    /// Registra a configuração do exchange para ser aplicada na primeira publicação (lazy).
    /// Evita conectar ao broker no construtor e permite que serviços iniciados por requisição RabbitMQ
    /// só conectem quando de fato publicarem uma mensagem.
    /// </summary>
    public void ConfigureExchange(
        string exchangeName,
        string exchangeType,
        bool durable = true,
        bool autoDelete = false,
        string? dlqExchangeName = null)
    {
        _pendingExchangeConfigs.Enqueue(new ExchangeConfig(exchangeName, exchangeType, durable, autoDelete, dlqExchangeName));
    }

    private void ApplyPendingExchangeConfigs()
    {
        if (_exchangeConfigsApplied)
            return;

        lock (_pendingExchangeConfigs)
        {
            if (_exchangeConfigsApplied)
                return;

            EnsureConnection();

            while (_pendingExchangeConfigs.TryDequeue(out ExchangeConfig config))
            {
                try
                {
                    if (!string.IsNullOrWhiteSpace(config.DlqExchangeName))
                    {
                        Channel?.ExchangeDeclare(
                            exchange: config.DlqExchangeName,
                            type: config.ExchangeType,
                            durable: config.Durable,
                            autoDelete: config.AutoDelete,
                            arguments: new Dictionary<string, object> { { "message-ttl", TimeSpan.FromDays(1).TotalMilliseconds } }
                        );
                    }

                    Channel?.ExchangeDeclare(
                        exchange: config.ExchangeName,
                        type: config.ExchangeType,
                        durable: config.Durable,
                        autoDelete: config.AutoDelete,
                        arguments: null
                    );
                    if (Logger.IsEnabled(LogLevel.Debug))
                    {
                        Logger.LogDebug("Exchange {ExchangeName} - {ExchangeType} configurada", config.ExchangeName, config.ExchangeType);
                    }
                }
                catch (Exception ex)
                {
                    Logger.LogError(ex, "Erro ao configurar Exchange no RabbitMQ: {ErrorMessage}", ex.Message);
                    throw;
                }
            }

            _exchangeConfigsApplied = true;
        }
    }

    public void PublishMessage(object message, string exchange, string routingKey)
    {
        try
        {
            ApplyPendingExchangeConfigs();
            EnsureConnection();
            Channel?.BasicPublish(
                exchange: exchange,
                routingKey: routingKey,
                basicProperties: null,
                body: JsonSerializer.SerializeToUtf8Bytes(message)
            );
        }
        catch (Exception ex)
        {
            Logger.LogError(ex, "Erro ao publicar mensagem no RabbitMQ: {ErrorMessage}", ex.Message);
            throw;
        }
    }

    private readonly record struct ExchangeConfig(
        string ExchangeName,
        string ExchangeType,
        bool Durable,
        bool AutoDelete,
        string? DlqExchangeName);
}