namespace Vigia.Cloud.Contracts;

public sealed class CloudObjectRead : IAsyncDisposable, IDisposable
{
    public CloudObjectRead(Stream body, long totalLength, long start, long end)
    {
        Body = body;
        TotalLength = totalLength;
        Start = start;
        End = end;
    }

    public Stream Body { get; }
    public long TotalLength { get; }
    public long Start { get; }
    public long End { get; }

    public void Dispose() => Body.Dispose();

    public ValueTask DisposeAsync() => Body.DisposeAsync();
}
