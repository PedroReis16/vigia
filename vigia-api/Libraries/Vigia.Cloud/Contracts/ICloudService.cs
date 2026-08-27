namespace Vigia.Cloud.Contracts;

public interface ICloudService
{
    Task EnsureBucketAsync(string bucketName, CancellationToken cancellationToken = default);

    Task UploadFileAsync(
        string bucketName,
        string key,
        Stream content,
        string? contentType = null,
        CancellationToken cancellationToken = default);

    Task<Stream> DownloadFileAsync(
        string bucketName,
        string key,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<string>> ListKeysAsync(
        string bucketName,
        CancellationToken cancellationToken = default);

    Task DeleteFileAsync(
        string bucketName,
        string key,
        CancellationToken cancellationToken = default);
}
