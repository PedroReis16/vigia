using System.Text.Json;
using RabbitMQ.Client.Events;
using Vigia.AMQP.Config;
using Vigia.AMQP.Configuration;
using Vigia.AMQP.Contracts;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Users;

namespace Vigia.API.Services;

internal sealed class KeycloakUserSyncConsumer(
    ISubscriberService subscriber,
    IServiceScopeFactory scopeFactory,
    ILogger<KeycloakUserSyncConsumer> logger) : BackgroundService
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    private readonly ISubscriberService _subscriber = subscriber;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;
    private readonly ILogger<KeycloakUserSyncConsumer> _logger = logger;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                _subscriber.ConsumeQueue(
                    exchangeName: ExchangeNames.UserSync,
                    queueName: QueueNames.UserSync,
                    routingKey: RoutingKeyNames.UserSync,
                    onNewMessage: OnMessageAsync,
                    dlqExchangeName: ExchangeNames.UserSyncDlq,
                    dlqQueueName: QueueNames.UserSyncDlq,
                    dlqRoutingKeyName: RoutingKeyNames.UserSyncDlq,
                    deliveryLimit: 2,
                    prefetchCount: 10);
                break;
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                _logger.LogError(ex, "Não foi possível consumir a fila de sincronização de usuários. Nova tentativa em 5s.");
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
            }
        }

        try
        {
            await Task.Delay(Timeout.Infinite, stoppingToken);
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
        {
        }
    }

    private async Task OnMessageAsync(object sender, BasicDeliverEventArgs args)
    {
        try
        {
            KeycloakUserSyncMessage? message = JsonSerializer.Deserialize<KeycloakUserSyncMessage>(args.Body.Span, JsonOptions);
            if (message is null)
            {
                _subscriber.Nack(args.DeliveryTag, requeue: false);
                return;
            }

            using IServiceScope scope = _scopeFactory.CreateScope();
            IKeycloakUserSyncService sync = scope.ServiceProvider.GetRequiredService<IKeycloakUserSyncService>();
            await sync.ApplyAsync(message);
            _subscriber.Ack(args.DeliveryTag);
            _logger.LogInformation(
                "Usuário {UserId} sincronizado a partir do Keycloak ({Operation}).",
                message.Id,
                message.Operation);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Falha ao sincronizar usuário a partir do RabbitMQ.");
            try
            {
                _subscriber.Nack(args.DeliveryTag, requeue: true);
            }
            catch (Exception nackEx)
            {
                _logger.LogError(nackEx, "Falha ao devolver a mensagem de sincronização para a fila.");
            }
        }
    }
}
