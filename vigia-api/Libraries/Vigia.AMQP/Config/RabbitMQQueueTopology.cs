using Vigia.AMQP.Configuration;
using RabbitMQ.Client;

namespace Vigia.AMQP.Configuration;

/// <summary>
/// Declaração idempotente de exchange/fila/binding em um canal RabbitMQ.
/// </summary>
public static class RabbitMQQueueTopology
{
    public static void Ensure(
        IModel channel,
        string exchangeName,
        string queueName,
        string routingKey,
        string? dlqExchangeName = null,
        string? dlqQueueName = null,
        string? dlqRoutingKeyName = null,
        int deliveryLimit = 2)
    {

        string exchangeType = ExchangeNames.GetExchangeType(exchangeName);

        channel.ExchangeDeclare(
            exchange: exchangeName,
            type: exchangeType,
            durable: true,
            autoDelete: false,
            arguments: null);

        bool hasDlq =
            !string.IsNullOrWhiteSpace(dlqExchangeName) &&
            !string.IsNullOrWhiteSpace(dlqQueueName) &&
            !string.IsNullOrWhiteSpace(dlqRoutingKeyName);

        if (hasDlq)
        {
            channel.ExchangeDeclare(
                exchange: dlqExchangeName!,
                type: exchangeType,
                durable: true,
                autoDelete: false,
                arguments: new Dictionary<string, object>
                {
                    { "message-ttl", TimeSpan.FromDays(1).TotalMilliseconds }
                });

            channel.QueueDeclare(
                queue: dlqQueueName!,
                durable: true,
                exclusive: false,
                autoDelete: false,
                arguments: null);

            channel.QueueBind(
                queue: dlqQueueName!,
                exchange: dlqExchangeName!,
                routingKey: dlqRoutingKeyName!);
        }

        IDictionary<string, object>? queueArguments = hasDlq
            ? new Dictionary<string, object>
            {
                { "x-queue-type", "quorum" },
                { "x-dead-letter-exchange", dlqExchangeName! },
                { "x-dead-letter-routing-key", dlqRoutingKeyName! },
                { "x-delivery-limit", deliveryLimit }
            }
            : null;

        channel.QueueDeclare(
            queue: queueName,
            durable: true,
            exclusive: false,
            autoDelete: false,
            arguments: queueArguments);

        channel.QueueBind(
            queue: queueName,
            exchange: exchangeName,
            routingKey: routingKey);
    }
}