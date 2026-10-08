using System.Collections.Concurrent;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts.Clips;
using Vigia.API.Models.DTOs.Devices;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Database.Contracts;
using Vigia.Models.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services.Clips;

internal sealed class ClipIngestService(
    IDeviceClipDao clips,
    IDevicesDao devices,
    ICloudService cloud,
    IClipAccessTokenProvider clipAccess,
    IClipAssembler assembler,
    IOptions<ClipOptions> options,
    IOptions<CloudOptions> cloudOptions,
    IClipAssemblyQueue queue,
    ILogger<ClipIngestService> logger) : IClipIngestService
{
    public const int MaxFrameCount = 4096;
    public const int MaxPngBytes = 8 * 1024 * 1024;

    private static readonly byte[] PngSignature = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A];
    private static readonly ConcurrentDictionary<Guid, SemaphoreSlim> Gates = new();
    private static readonly ConcurrentDictionary<Guid, SemaphoreSlim> PosterGates = new();

    private readonly IDeviceClipDao _clips = clips;
    private readonly IDevicesDao _devices = devices;
    private readonly ICloudService _cloud = cloud;
    private readonly IClipAccessTokenProvider _clipAccess = clipAccess;
    private readonly IClipAssembler _assembler = assembler;
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
        string directory;
        await gate.WaitAsync(cancellationToken);
        try
        {
            directory = await RequireOpenSessionAsync(deviceId, clipId, index, cancellationToken);
        }
        finally
        {
            gate.Release();
        }

        string? partial = null;
        try
        {
            partial = await ClipStaging.WritePartialAsync(directory, index, bytes, cancellationToken);
            await gate.WaitAsync(cancellationToken);
            try
            {
                DeviceClip clip = await RequireOpenClipAsync(deviceId, clipId, index, cancellationToken);
                ClipStaging.CommitFrame(partial, ClipStaging.FramePath(directory, index));
                partial = null;

                if (!ClipStaging.HasAllFrames(directory, clip.FrameCount))
                    return;

                if (!await _clips.TryMarkAssemblingAsync(clipId, cancellationToken))
                    return;

                _queue.Enqueue(new ClipAssemblyJob(deviceId, clipId, clip.Fps, directory, clip.FrameCount));
                _logger.LogInformation(
                    "Clipe {ClipId} completo ({FrameCount} frames); reorganização enfileirada",
                    clipId,
                    clip.FrameCount);
            }
            finally
            {
                gate.Release();
            }
        }
        finally
        {
            ClipStaging.DeleteFileQuietly(partial);
        }
    }

    private async Task<string> RequireOpenSessionAsync(
        Guid deviceId,
        Guid clipId,
        int index,
        CancellationToken cancellationToken)
    {
        await RequireOpenClipAsync(deviceId, clipId, index, cancellationToken);
        return ClipStaging.SessionDirectory(_options, deviceId, clipId);
    }

    private async Task<DeviceClip> RequireOpenClipAsync(
        Guid deviceId,
        Guid clipId,
        int index,
        CancellationToken cancellationToken)
    {
        DeviceClip? clip = await _clips.FindAsync(clipId, cancellationToken);
        if (clip == null || clip.DeviceId != deviceId)
            throw new HttpResponseException(StatusCodes.Status404NotFound, "Sessão de clipe não encontrada", ErrorCodes.CLIP_NOT_FOUND);

        if (clip.Status != ClipStatus.Receiving)
            throw new HttpResponseException(StatusCodes.Status409Conflict, "A sessão do clipe já foi encerrada", ErrorCodes.CLIP_SESSION_CLOSED);

        if (index < 0 || index >= clip.FrameCount)
            throw new HttpResponseException(StatusCodes.Status400BadRequest, "O índice do frame está fora da sequência", ErrorCodes.CLIP_FRAME_INDEX_INVALID);

        return clip;
    }

    public async Task<List<DeviceClipDTO>> ListAsync(Guid deviceId, Guid userId, CancellationToken cancellationToken = default)
    {
        if (await _devices.FindAsync(deviceId) == null)
            throw new HttpResponseException(StatusCodes.Status404NotFound, "Dispositivo não encontrado", ErrorCodes.DEVICE_NOT_FOUND);

        List<DeviceClip> clips = await _clips.ListByDeviceAsync(deviceId, cancellationToken);
        string? accessToken = null;
        List<DeviceClipDTO> result = [];
        foreach (DeviceClip clip in clips)
        {
            DeviceClipDTO dto = new()
            {
                Id = clip.Id,
                DeviceId = clip.DeviceId,
                Status = clip.Status,
                FrameCount = clip.FrameCount,
                Fps = clip.Fps,
                CreatedAt = clip.CreatedAt,
            };

            if (clip.Status == ClipStatus.Ready && !string.IsNullOrWhiteSpace(clip.ObjectKey))
            {
                accessToken ??= _clipAccess.IssueToken(userId, deviceId);
                dto.PlaybackUrl = $"devices/{deviceId:D}/clips/{clip.Id:D}?accessToken={accessToken}";
                dto.ThumbnailUrl = $"devices/{deviceId:D}/clips/{clip.Id:D}/thumbnail?accessToken={accessToken}";
            }

            result.Add(dto);
        }

        return result;
    }

    public async Task<long?> GetVideoLengthAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken = default)
    {
        DeviceClip? clip = await FindReadyClipAsync(deviceId, clipId, cancellationToken);
        if (clip == null || string.IsNullOrWhiteSpace(clip.ObjectKey))
            return null;

        EnsurePicturesBucket();
        return await _cloud.TryGetObjectLengthAsync(_cloudOptions.PicturesBucketName, clip.ObjectKey, cancellationToken);
    }

    public async Task<CloudObjectRead?> OpenVideoAsync(
        Guid deviceId,
        Guid clipId,
        long? start,
        long? end,
        CancellationToken cancellationToken = default)
    {
        DeviceClip? clip = await FindReadyClipAsync(deviceId, clipId, cancellationToken);
        if (clip == null || string.IsNullOrWhiteSpace(clip.ObjectKey))
            return null;

        EnsurePicturesBucket();
        try
        {
            return await _cloud.OpenRangeAsync(_cloudOptions.PicturesBucketName, clip.ObjectKey, start, end, cancellationToken);
        }
        catch (FileNotFoundException)
        {
            return null;
        }
    }

    public async Task<Stream?> OpenThumbnailAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken = default)
    {
        DeviceClip? clip = await FindReadyClipAsync(deviceId, clipId, cancellationToken);
        if (clip == null || string.IsNullOrWhiteSpace(clip.ObjectKey))
            return null;

        EnsurePicturesBucket();
        string posterKey = ClipObjectKeys.Poster(deviceId, clipId);
        SemaphoreSlim gate = PosterGates.GetOrAdd(clipId, _ => new SemaphoreSlim(1, 1));
        await gate.WaitAsync(cancellationToken);
        try
        {
            if (!await PosterExistsAsync(deviceId, clipId, cancellationToken))
                await CreatePosterFromVideoAsync(clip, posterKey, cancellationToken);

            return await _cloud.DownloadFileAsync(_cloudOptions.PicturesBucketName, posterKey, cancellationToken);
        }
        catch (Exception ex) when (ex is FileNotFoundException or InvalidOperationException)
        {
            _logger.LogWarning(ex, "Não foi possível obter o poster do clipe {ClipId}", clipId);
            return null;
        }
        finally
        {
            gate.Release();
        }
    }

    private async Task CreatePosterFromVideoAsync(DeviceClip clip, string posterKey, CancellationToken cancellationToken)
    {
        string directory = Path.Combine(Path.GetTempPath(), "vigia-poster", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            string videoPath = Path.Combine(directory, "clip.mp4");
            string posterPath = Path.Combine(directory, "poster.jpg");
            await using (FileStream file = File.Create(videoPath))
            await using (Stream video = await _cloud.DownloadFileAsync(_cloudOptions.PicturesBucketName, clip.ObjectKey!, cancellationToken))
                await video.CopyToAsync(file, cancellationToken);

            await _assembler.WritePosterFromVideoAsync(videoPath, posterPath, cancellationToken);

            await using FileStream poster = File.OpenRead(posterPath);
            await _cloud.UploadFileAsync(
                _cloudOptions.PicturesBucketName,
                posterKey,
                poster,
                "image/jpeg",
                cancellationToken);
        }
        finally
        {
            try
            {
                Directory.Delete(directory, recursive: true);
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Não foi possível remover o poster temporário de {Directory}", directory);
            }
        }
    }

    private async Task<DeviceClip?> FindReadyClipAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken)
    {
        DeviceClip? clip = await _clips.FindAsync(clipId, cancellationToken);
        if (clip == null || clip.DeviceId != deviceId || clip.Status != ClipStatus.Ready)
            return null;

        return clip;
    }

    private async Task<bool> PosterExistsAsync(Guid deviceId, Guid clipId, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(_cloudOptions.PicturesBucketName))
            return false;

        try
        {
            long? length = await _cloud.TryGetObjectLengthAsync(
                _cloudOptions.PicturesBucketName,
                ClipObjectKeys.Poster(deviceId, clipId),
                cancellationToken);
            return length is > 0;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Não foi possível verificar o poster do clipe {ClipId}", clipId);
            return false;
        }
    }

    private void EnsurePicturesBucket()
    {
        if (string.IsNullOrWhiteSpace(_cloudOptions.PicturesBucketName))
            throw new HttpResponseException(StatusCodes.Status500InternalServerError, "O bucket de pictures não está configurado", ErrorCodes.UNKNOWN_ERROR);
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
