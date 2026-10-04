using System.Collections.Concurrent;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts.Clips;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Database.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services.Clips;

internal sealed class ClipIngestService(
    IDeviceClipDao clips,
    IDevicesDao devices,
    ICloudService cloud,
    IOptions<ClipOptions> options,
    IOptions<CloudOptions> cloudOptions,
    IClipAssemblyQueue queue,
    ILogger<ClipIngestService> logger) : IClipIngestService
{
    public const int MaxFrameCount = 4096;
    public const int MaxPngBytes = 8 * 1024 * 1024;

    private static readonly byte[] PngSignature = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A];
    private static readonly ConcurrentDictionary<Guid, SemaphoreSlim> Gates = new();

    private readonly IDeviceClipDao _clips = clips;
    private readonly IDevicesDao _devices = devices;
    private readonly ICloudService _cloud = cloud;
    private readonly ClipOptions _options = options.Value;
    private readonly CloudOptions _cloudOptions = cloudOptions.Value;
    private readonly IClipAssemblyQueue _queue = queue;
    private readonly ILogger<ClipIngestService> _logger = logger;

    public async Task OpenSessionAsync(Guid deviceId, OpenClipSessionDTO session, CancellationToken cancellationToken = default)
    {
        if (session.ClipId == Guid.Empty)
            throw new HttpResponseException(StatusCodes.Status400BadRequest, "O identificador do clipe é obrigatório", ErrorCodes.VALIDATION_ERROR);

        if (session.FrameCount < 1 || session.FrameCount > MaxFrameCount)
            throw new HttpResponseException(StatusCodes.Status400BadRequest, "A quantidade de frames do clipe é inválida", ErrorCodes.VALIDATION_ERROR);

        if (session.Fps < 1)
            throw new HttpResponseException(StatusCodes.Status400BadRequest, "O fps do clipe é inválido", ErrorCodes.VALIDATION_ERROR);

        if (await _devices.FindAsync(deviceId) == null)
            throw new HttpResponseException(StatusCodes.Status404NotFound, "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

        SemaphoreSlim gate = Gates.GetOrAdd(session.ClipId, _ => new SemaphoreSlim(1, 1));
        await gate.WaitAsync(cancellationToken);
        try
        {
            DeviceClip? existing = await _clips.FindAsync(session.ClipId, cancellationToken);
            if (existing != null)
            {
                if (existing.DeviceId != deviceId)
                    throw new HttpResponseException(StatusCodes.Status409Conflict, "O clipe pertence a outro dispositivo", ErrorCodes.CLIP_SESSION_CLOSED);

                if (existing.Status != ClipStatus.Receiving)
                    throw new HttpResponseException(StatusCodes.Status409Conflict, "A sessão do clipe já foi encerrada", ErrorCodes.CLIP_SESSION_CLOSED);

                if (existing.FrameCount != session.FrameCount || existing.Fps != session.Fps)
                    throw new HttpResponseException(StatusCodes.Status409Conflict, "A sessão do clipe já foi aberta com outros parâmetros", ErrorCodes.CLIP_SESSION_CLOSED);

                return;
            }

            string directory = ClipStaging.SessionDirectory(_options, deviceId, session.ClipId);
            Directory.CreateDirectory(directory);

            await _clips.AddAsync(new DeviceClip
            {
                Id = session.ClipId,
                DeviceId = deviceId,
                Status = ClipStatus.Receiving,
                FrameCount = session.FrameCount,
                Fps = session.Fps,
                CreatedAt = DateTime.UtcNow,
            }, cancellationToken);

            _logger.LogInformation(
                "Sessão de clipe {ClipId} aberta para o dispositivo {DeviceId} ({FrameCount} frames)",
                session.ClipId,
                deviceId,
                session.FrameCount);
        }
        finally
        {
            gate.Release();
        }
    }

    public async Task SaveFrameAsync(Guid deviceId, Guid clipId, int index, Stream png, CancellationToken cancellationToken = default)
    {
        byte[] bytes = await ReadPngAsync(png, cancellationToken);
        if (!IsPng(bytes))
            throw new HttpResponseException(StatusCodes.Status400BadRequest, "O frame não é um PNG válido", ErrorCodes.INVALID_CLIP_FRAME);

        SemaphoreSlim gate = Gates.GetOrAdd(clipId, _ => new SemaphoreSlim(1, 1));
        await gate.WaitAsync(cancellationToken);
        try
        {
            DeviceClip? clip = await _clips.FindAsync(clipId, cancellationToken);
            if (clip == null || clip.DeviceId != deviceId)
                throw new HttpResponseException(StatusCodes.Status404NotFound, "Sessão de clipe não encontrada", ErrorCodes.CLIP_NOT_FOUND);

            if (clip.Status != ClipStatus.Receiving)
                throw new HttpResponseException(StatusCodes.Status409Conflict, "A sessão do clipe já foi encerrada", ErrorCodes.CLIP_SESSION_CLOSED);

            if (index < 0 || index >= clip.FrameCount)
                throw new HttpResponseException(StatusCodes.Status400BadRequest, "O índice do frame está fora da sequência", ErrorCodes.CLIP_FRAME_INDEX_INVALID);

            string directory = ClipStaging.SessionDirectory(_options, deviceId, clipId);
            Directory.CreateDirectory(directory);
            string framePath = ClipStaging.FramePath(directory, index);
            await File.WriteAllBytesAsync(framePath, bytes, cancellationToken);

            if (!ClipStaging.HasAllFrames(directory, clip.FrameCount))
                return;

            if (!await _clips.TryMarkAssemblingAsync(clipId, cancellationToken))
                return;

            _queue.Enqueue(new ClipAssemblyJob(deviceId, clipId, clip.Fps, directory));
            _logger.LogInformation("Clipe {ClipId} completo; montagem enfileirada", clipId);
        }
        finally
        {
            gate.Release();
        }
    }

    public async Task<List<DeviceClipDTO>> ListAsync(Guid deviceId, CancellationToken cancellationToken = default)
    {
        if (await _devices.FindAsync(deviceId) == null)
            throw new HttpResponseException(StatusCodes.Status404NotFound, "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

        List<DeviceClip> clips = await _clips.ListByDeviceAsync(deviceId, cancellationToken);
        return clips.Select(clip => new DeviceClipDTO
        {
            Id = clip.Id,
            DeviceId = clip.DeviceId,
            Status = clip.Status,
            FrameCount = clip.FrameCount,
            Fps = clip.Fps,
            CreatedAt = clip.CreatedAt,
        }).ToList();
    }

    public async Task<Stream?> OpenVideoAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken = default)
    {
        DeviceClip? clip = await _clips.FindAsync(clipId, cancellationToken);
        if (clip == null || clip.DeviceId != deviceId || clip.Status != ClipStatus.Ready || string.IsNullOrWhiteSpace(clip.ObjectKey))
            return null;

        if (string.IsNullOrWhiteSpace(_cloudOptions.PicturesBucketName))
            throw new HttpResponseException(StatusCodes.Status500InternalServerError, "O bucket de pictures não está configurado", ErrorCodes.UNKNOWN_ERROR);

        return await _cloud.DownloadFileAsync(_cloudOptions.PicturesBucketName, clip.ObjectKey, cancellationToken);
    }

    internal static bool IsPng(ReadOnlySpan<byte> bytes)
    {
        return bytes.Length >= PngSignature.Length && bytes[..PngSignature.Length].SequenceEqual(PngSignature);
    }

    private static async Task<byte[]> ReadPngAsync(Stream png, CancellationToken cancellationToken)
    {
        using MemoryStream buffer = new();
        byte[] chunk = new byte[81920];
        while (true)
        {
            int read = await png.ReadAsync(chunk, cancellationToken);
            if (read == 0)
                break;

            if (buffer.Length + read > MaxPngBytes)
                throw new HttpResponseException(StatusCodes.Status400BadRequest, "O frame PNG excede o tamanho máximo", ErrorCodes.INVALID_CLIP_FRAME);

            buffer.Write(chunk, 0, read);
        }

        if (buffer.Length == 0)
            throw new HttpResponseException(StatusCodes.Status400BadRequest, "O frame PNG está vazio", ErrorCodes.INVALID_CLIP_FRAME);

        return buffer.ToArray();
    }
}
