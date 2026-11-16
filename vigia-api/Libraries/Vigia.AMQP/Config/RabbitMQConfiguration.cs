namespace Vigia.AMQP.Config;

public record RabbitMQConfiguration(
    string HostName,
    string Username,
    string Password,
    int Port = 5672
);