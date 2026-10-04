namespace Vigia.AMQP.Config;

public record RabbitMQConfiguration(
    string HostName,
    int Port = 5672,
    string Username,
    string Password
);