using System.Threading.Channels;
using Vigia.API.Contracts.Clips;

namespace Vigia.API.Services.Clips;

internal sealed class ClipAssemblyQueue : IClipAssemblyQueue
{
    private readonly Channel<ClipAssemblyJob> _channel = Channel.CreateUnbounded<ClipAssemblyJob>();

    public ChannelReader<ClipAssemblyJob> Reader => _channel.Reader;

    public void Enqueue(ClipAssemblyJob job)
    {
        if (!_channel.Writer.TryWrite(job))
            throw new InvalidOperationException("A fila de montagem de clipes está fechada");
    }
}
