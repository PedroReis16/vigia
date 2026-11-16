namespace Vigia.AMQP.Contracts;

public interface IQueueService : IDisposable
{
    void Initialize();
}