using Vigia.API.Contracts.Devices;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;

namespace Vigia.API.Services.Devices;

internal class VersionService(ILogger<VersionService> logger, IServiceScopeFactory scopeFactory) : IVersionService
{
    private readonly ILogger<VersionService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task UploadDeviceVersionAsync(string version, string filePath)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();

            IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();
            string versionBucket = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()!.VersionsBucketName!;

            using FileStream fileStream = File.OpenRead(filePath);
            await cloudService.UploadFileAsync(versionBucket, version, fileStream, "application/octet-stream");
        }
        catch (Exception ex)
        {
            string errorMessage = $"Error uploading device version: {ex.Message}";
            _logger.LogError(errorMessage);
            throw new Exception(errorMessage, ex);
        }
        finally
        {
            try
            {
                File.Delete(filePath);
            }
            catch (Exception ex)
            {
                string errorMessage = $"Error deleting file: {ex.Message}";
                _logger.LogError(errorMessage);
            }
        }
    }
}