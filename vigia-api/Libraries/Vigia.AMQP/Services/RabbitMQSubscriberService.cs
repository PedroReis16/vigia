using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Vigia.AMQP.Configuration;
using Vigia.AMQP.Contracts;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using RabbitMQ.Client.Exceptions;

namespace Vigia.AMQP.Services;

public class RabbitMQSubscriberService(ILogger<RabbitMQQueueService> logger, IConfiguration configuration) : RabbitMQQueueService(logger, configuration), ISubscriberService
{
    private readonly object _consumerSync = new();
    private readonly Dictionary<string, string> _consumerTagsByQueue = new(StringComparer.Ordinal);
    private bool _prefetchConfigured;

    public void ConsumeQueue(
        string exchangeName,
        string queueName,
        string routingKey,
        AsyncEventHandler<BasicDeliverEventArgs> onNewMessage,
        string? dlqExchangeName = null,
        string? dlqQueueName = null,
        string? dlqRoutingKeyName = null,
        int deliveryLimit = 2,
        ushort? prefetchCount = null,
        bool prefetchGlobal = false)
    {
        try
        {
            EnsureChannel();
            EnsurePrefetch(prefetchCount, prefetchGlobal);
            EnsureTopology(
                exchangeName: exchangeName,
                queueName: queueName,
                routingKey: routingKey,
                dlqExchangeName: dlqExchangeName,
                dlqQueueName: dlqQueueName,
                dlqRoutingKeyName: dlqRoutingKeyName,
                deliveryLimit: deliveryLimit);

            // Evita criar múltiplos consumidores se esse método for chamado em rotina
            lock (_consumerSync)
            {
                if (Channel != null && Channel.IsOpen && _consumerTagsByQueue.ContainsKey(queueName))
                    return;
            }

            AsyncEventingBasicConsumer consumer = new(Channel);
            consumer.Received += onNewMessage;

            string? consumerTag = Channel?.BasicConsume(
                queue: queueName,
                autoAck: false,
                consumer: consumer
            );

            if (!string.IsNullOrWhiteSpace(consumerTag))
            {
                lock (_consumerSync)
                {
                    _consumerTagsByQueue[queueName] = consumerTag;
                }
            }
        }
        catch (Exception ex)
        {
            Logger.LogError(ex, "Erro ao configurar Subscriber no RabbitMQ: {ErrorMessage}", ex.Message);
            throw;
        }
    }

    /// <summary>
    /// Garante (idempotente) que exchange/fila/binding existam, mesmo sem mensagens.
    /// Útil para evitar a perda da "primeira mensagem" quando a topologia ainda não foi criada.
    /// </summary>
    public void EnsureTopology(
        string exchangeName,
        string queueName,
        string routingKey,
        string? dlqExchangeName = null,
        string? dlqQueueName = null,
        string? dlqRoutingKeyName = null,
        int deliveryLimit = 2)
    {
        EnsureChannel();

        RabbitMQQueueTopology.Ensure(
            channel: Channel!,
            exchangeName: exchangeName,
            queueName: queueName,
            routingKey: routingKey,
            dlqExchangeName: dlqExchangeName,
            dlqQueueName: dlqQueueName,
            dlqRoutingKeyName: dlqRoutingKeyName,
            deliveryLimit: deliveryLimit);
    }

    private void EnsurePrefetch(ushort? prefetchCount, bool prefetchGlobal)
    {
        if (!prefetchCount.HasValue)
            return;

        lock (_consumerSync)
        {
            if (_prefetchConfigured)
                return;

            Channel?.BasicQos(prefetchSize: 0, prefetchCount: prefetchCount.Value, global: prefetchGlobal);
            _prefetchConfigured = true;
        }
    }

    private void EnsureChannel()
    {
        EnsureConnection();
        if (Channel == null || Channel.IsClosed)
        {
            Logger.LogWarning("Canal RabbitMQ está fechado ou nulo. Recriando canal...");
            RecreateChannel();
        }
    }

    private static string InferExchangeType(string exchangeName) => ExchangeNames.GetExchangeType(exchangeName);

    private void RecreateChannel()
    {
        try
        {
            Channel?.Dispose();
            Channel = null;

            if (Connection == null || !Connection.IsOpen)
            {
                Logger.LogWarning("Conexão RabbitMQ está fechada ou nula. Recriando conexão...");
                Connection?.Dispose();
                Connection = null;
                Initialize();
            }
            else
            {
                Channel = Connection.CreateModel();
                Logger.LogDebug("Canal RabbitMQ recriado com sucesso");
            }

            lock (_consumerSync)
            {
                _consumerTagsByQueue.Clear();
                _prefetchConfigured = false;
            }
        }
        catch (Exception ex)
        {
            Logger.LogError(ex, "Erro ao recriar canal RabbitMQ: {ErrorMessage}", ex.Message);
            throw;
        }
    }
}