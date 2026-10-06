using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts.Clips;
using Vigia.API.Models.DTOs.Devices;
using Vigia.API.Services.Clips;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.UnitTests;

public class ClipIngestServiceTests : IDisposable
{
    private static readonly byte[] Png = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00];

    private readonly string _staging = Path.Combine(Path.GetTempPath(), "vigia-clip-tests", Guid.NewGuid().ToString("N"));
    private readonly VigiaDbContext _context;
    private readonly RecordingQueue _queue = new();
    private readonly ClipIngestService _service;
    private readonly Guid _deviceId = Guid.NewGuid();

    public ClipIngestServiceTests()
    {
        Directory.CreateDirectory(_staging);
        _context = CreateContext();
        _context.Devices.Add(new Device
        {
            Id = _deviceId,
            Name = "Vigia-0123abcd",
            MacAddress = "aa:bb:cc:dd:ee:ff",
        });
        _context.SaveChanges();

        _service = new ClipIngestService(
            new DeviceClipDao(_context),
            new DevicesDao(_context),
            new UnusedCloud(),
            Options.Create(new ClipOptions { StagingDirectory = _staging, SessionTtlMinutes = 15 }),
            Options.Create(new CloudOptions { PicturesBucketName = "vigia-pictures" }),
            _queue,
            NullLogger<ClipIngestService>.Instance);
    }

    [Fact]
    public async Task SaveFrame_SoMontaQuandoASequenciaEstaCompleta()
    {
        Guid clipId = Guid.NewGuid();
        await _service.OpenSessionAsync(_deviceId, new OpenClipSessionDTO(clipId, 2, 12));

        await _service.SaveFrameAsync(_deviceId, clipId, 1, new MemoryStream(Png));
        Assert.Empty(_queue.Jobs);

        await _service.SaveFrameAsync(_deviceId, clipId, 0, new MemoryStream(Png));

        Assert.Single(_queue.Jobs);
        Assert.Equal(clipId, _queue.Jobs[0].ClipId);
        Assert.Equal(12, _queue.Jobs[0].Fps);
        Assert.Equal(2, _queue.Jobs[0].FrameCount);
        Assert.True(File.Exists(Path.Combine(_queue.Jobs[0].StagingDirectory, "000000.png")));
        Assert.True(File.Exists(Path.Combine(_queue.Jobs[0].StagingDirectory, "000001.png")));

        DeviceClip stored = await _context.DeviceClips.SingleAsync(clip => clip.Id == clipId);
        Assert.Equal(ClipStatus.Assembling, stored.Status);
    }

    [Fact]
    public async Task SaveFrame_RejeitaIndiceForaDaSequencia()
    {
        Guid clipId = Guid.NewGuid();
        await _service.OpenSessionAsync(_deviceId, new OpenClipSessionDTO(clipId, 2, 12));

        HttpResponseException error = await Assert.ThrowsAsync<HttpResponseException>(
            () => _service.SaveFrameAsync(_deviceId, clipId, 2, new MemoryStream(Png)));

        Assert.Equal(StatusCodes.Status400BadRequest, error.StatusCode);
        Assert.Equal(ErrorCodes.CLIP_FRAME_INDEX_INVALID, error.ErrorCode);
        Assert.Empty(_queue.Jobs);
    }

    [Fact]
    public void ArrangeSequence_CopiaNaOrdemDoIndice()
    {
        string session = Path.Combine(_staging, "arrange");
        Directory.CreateDirectory(session);
        File.WriteAllBytes(Path.Combine(session, "000001.png"), [0x01]);
        File.WriteAllBytes(Path.Combine(session, "000000.png"), [0x00]);

        string ordered = ClipStaging.ArrangeSequence(session, 2);

        Assert.Equal((byte)0x00, File.ReadAllBytes(Path.Combine(ordered, "000000.png"))[0]);
        Assert.Equal((byte)0x01, File.ReadAllBytes(Path.Combine(ordered, "000001.png"))[0]);
    }

    [Fact]
    public void ArrangeSequence_SequenciaIncompleta_Falha()
    {
        string session = Path.Combine(_staging, "incomplete");
        Directory.CreateDirectory(session);
        File.WriteAllBytes(Path.Combine(session, "000001.png"), Png);

        Assert.Throws<InvalidOperationException>(() => ClipStaging.ArrangeSequence(session, 2));
    }

    [Fact]
    public async Task SaveFrame_RejeitaPngInvalido()
    {
        Guid clipId = Guid.NewGuid();
        await _service.OpenSessionAsync(_deviceId, new OpenClipSessionDTO(clipId, 1, 12));

        HttpResponseException error = await Assert.ThrowsAsync<HttpResponseException>(
            () => _service.SaveFrameAsync(_deviceId, clipId, 0, new MemoryStream([0x00, 0x01, 0x02])));

        Assert.Equal(StatusCodes.Status400BadRequest, error.StatusCode);
        Assert.Equal(ErrorCodes.INVALID_CLIP_FRAME, error.ErrorCode);
        Assert.Empty(_queue.Jobs);
    }

    public void Dispose()
    {
        _context.Dispose();
        if (Directory.Exists(_staging))
            Directory.Delete(_staging, recursive: true);
    }

    private static VigiaDbContext CreateContext()
    {
        DbContextOptions<VigiaDbContext> options = new DbContextOptionsBuilder<VigiaDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        VigiaDbContext context = new(options);
        context.Database.EnsureCreated();
        return context;
    }

    private sealed class RecordingQueue : IClipAssemblyQueue
    {
        public List<ClipAssemblyJob> Jobs { get; } = [];

        public void Enqueue(ClipAssemblyJob job) => Jobs.Add(job);
    }

    private sealed class UnusedCloud : ICloudService
    {
        public Task EnsureBucketAsync(string bucketName, CancellationToken cancellationToken = default) => Task.CompletedTask;

        public Task UploadFileAsync(string bucketName, string key, Stream content, string? contentType = null, CancellationToken cancellationToken = default) =>
            Task.CompletedTask;

        public Task<Stream> DownloadFileAsync(string bucketName, string key, CancellationToken cancellationToken = default) =>
            throw new NotSupportedException();

        public Task<IReadOnlyList<string>> ListKeysAsync(string bucketName, CancellationToken cancellationToken = default) =>
            Task.FromResult<IReadOnlyList<string>>([]);

        public Task DeleteFileAsync(string bucketName, string key, CancellationToken cancellationToken = default) =>
            Task.CompletedTask;
    }
}
