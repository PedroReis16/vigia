using Microsoft.Extensions.DependencyInjection;
using Vigia.AMQP.Contracts;
using Vigia.AMQP.Services;

namespace Vigia.AMQP.Extensions;

public static class AmqpExtension
{
    public static IServiceCollection AddRabbitMq(this IServiceCollection services)
    {
        services.AddSingleton<ISubscriberService, RabbitMQSubscriberService>();
        return services;
    }
}
