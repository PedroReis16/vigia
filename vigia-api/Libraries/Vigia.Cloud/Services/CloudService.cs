using Amazon.S3;
using Amazon.S3.Model;
using Vigia.Cloud.Contracts;

namespace Vigia.Cloud.Services;

internal class CloudService(IAmazonS3 s3Client) : ICloudService
{
    private readonly IAmazonS3 _s3Client = s3Client;

    public async Task EnsureBucketAsync(string bucketName, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(bucketName);

        ListBucketsResponse buckets = await _s3Client.ListBucketsAsync(cancellationToken);
        bool exists = buckets.Buckets.Exists(b =>
            string.Equals(b.BucketName, bucketName, StringComparison.Ordinal));

        if (exists)
        {
            return;
        }

        await _s3Client.PutBucketAsync(new PutBucketRequest
        {
            BucketName = bucketName,
        }, cancellationToken);
    }

    public async Task UploadFileAsync(
        string bucketName,
        string key,
        Stream content,
        string? contentType = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(bucketName);
        ArgumentException.ThrowIfNullOrWhiteSpace(key);
        ArgumentNullException.ThrowIfNull(content);

        var request = new PutObjectRequest
        {
            BucketName = bucketName,
            Key = key,
            InputStream = content,
            AutoCloseStream = false,
        };

        if (!string.IsNullOrWhiteSpace(contentType))
        {
            request.ContentType = contentType;
        }

        await _s3Client.PutObjectAsync(request, cancellationToken);
    }
}
