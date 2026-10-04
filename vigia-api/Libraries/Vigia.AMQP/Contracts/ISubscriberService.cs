using RabbitMQ.Client.Events;

namespace Vigia.AMQP.Contracts;

public interface ISubscriberService : IQueueService
{
    void ConsumeQueue(
        string exchangeName,
        string queueName,
        string routingKey,
        AsyncEventHandler<BasicDeliverEventArgs> onNewMessage,
        string? dlqExchangeName = null,
        string? dlqQueueName = null,
        string? dlqRoutingKeyName = null,
        int deliveryLimit = 3,
        ushort? prefetchCount = null,
        bool prefetchGlobal = false);

    void Ack(ulong deliveryTag);

    void Nack(ulong deliveryTag, bool requeue);
}