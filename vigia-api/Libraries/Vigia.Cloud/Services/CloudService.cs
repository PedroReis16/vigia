using System.Net;
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

    public async Task<Stream> DownloadFileAsync(
        string bucketName,
        string key,
        CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(bucketName);
        ArgumentException.ThrowIfNullOrWhiteSpace(key);

        try
        {
            GetObjectResponse response = await _s3Client.GetObjectAsync(new GetObjectRequest
            {
                BucketName = bucketName,
                Key = key,
            }, cancellationToken);

            return new S3DownloadStream(response);
        }
        catch (AmazonS3Exception ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            throw new FileNotFoundException($"Object '{key}' was not found in bucket '{bucketName}'.", ex);
        }
    }

    public async Task<IReadOnlyList<string>> ListKeysAsync(
        string bucketName,
        CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(bucketName);

        List<string> keys = [];
        string? continuationToken = null;

        do
        {
            ListObjectsV2Response response = await _s3Client.ListObjectsV2Async(new ListObjectsV2Request
            {
                BucketName = bucketName,
                ContinuationToken = continuationToken,
            }, cancellationToken);

            foreach (S3Object obj in response.S3Objects)
            {
                if (!string.IsNullOrWhiteSpace(obj.Key))
                    keys.Add(obj.Key);
            }

            continuationToken = response.IsTruncated == true
                ? response.NextContinuationToken
                : null;
        }
        while (continuationToken is not null);

        return keys;
    }

    /// <summary>
    /// Owns the <see cref="GetObjectResponse"/> so the response stream stays valid until disposed.
    /// </summary>
    private sealed class S3DownloadStream : Stream
    {
        private readonly GetObjectResponse _response;
        private readonly Stream _inner;
        private bool _disposed;

        public S3DownloadStream(GetObjectResponse response)
        {
            _response = response;
            _inner = response.ResponseStream;
        }

        public override bool CanRead => _inner.CanRead;
        public override bool CanSeek => _inner.CanSeek;
        public override bool CanWrite => _inner.CanWrite;
        public override long Length => _inner.Length;
        public override long Position
        {
            get => _inner.Position;
            set => _inner.Position = value;
        }

        public override void Flush() => _inner.Flush();
        public override Task FlushAsync(CancellationToken cancellationToken) => _inner.FlushAsync(cancellationToken);
        public override int Read(byte[] buffer, int offset, int count) => _inner.Read(buffer, offset, count);
        public override Task<int> ReadAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken) =>
            _inner.ReadAsync(buffer, offset, count, cancellationToken);
        public override ValueTask<int> ReadAsync(Memory<byte> buffer, CancellationToken cancellationToken = default) =>
            _inner.ReadAsync(buffer, cancellationToken);
        public override long Seek(long offset, SeekOrigin origin) => _inner.Seek(offset, origin);
        public override void SetLength(long value) => _inner.SetLength(value);
        public override void Write(byte[] buffer, int offset, int count) => _inner.Write(buffer, offset, count);

        protected override void Dispose(bool disposing)
        {
            if (_disposed)
                return;

            if (disposing)
            {
                _inner.Dispose();
                _response.Dispose();
            }

            _disposed = true;
            base.Dispose(disposing);
        }

        public override async ValueTask DisposeAsync()
        {
            if (_disposed)
                return;

            await _inner.DisposeAsync();
            _response.Dispose();
            _disposed = true;
            await base.DisposeAsync();
        }
    }
}
