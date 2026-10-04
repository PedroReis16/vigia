namespace Vigia.AMQP.Contracts;

public interface IPublisherService : IQueueService
{
    void ConfigureExchange(
        string exchangeName,
        string exchangeType,
        bool durable = true,
        bool autoDelete = false,
        string? dlqExchangeName = null);

    void PublishMessage(object message, string exchange, string routingKey);
}