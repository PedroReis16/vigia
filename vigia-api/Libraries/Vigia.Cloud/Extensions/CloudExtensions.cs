using Amazon;
using Amazon.Runtime;
using Amazon.S3;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Cloud.Services;
using Vigia.Cloud.BackgroundJob;
using Microsoft.Extensions.Hosting;

namespace Vigia.Cloud.Extensions;

public static class CloudExtensions
{
    public static IServiceCollection AddCloudServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.Configure<CloudOptions>(configuration.GetSection(CloudOptions.SectionName));

        services.AddSingleton<IAmazonS3>(sp =>
        {
            CloudOptions options = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()
                ?? new CloudOptions();

            var config = new AmazonS3Config
            {
                ForcePathStyle = options.UsePathStyle,
                AuthenticationRegion = options.Region,
            };

            if (!string.IsNullOrWhiteSpace(options.Endpoint))
            {
                config.ServiceURL = NormalizeEndpoint(options.Endpoint);
            }
            else if (!string.IsNullOrWhiteSpace(options.Region))
            {
                config.RegionEndpoint = RegionEndpoint.GetBySystemName(options.Region);
            }

            var credentials = new BasicAWSCredentials(options.AccessKey, options.SecretKey);
            return new AmazonS3Client(credentials, config);
        });

        services.AddTransient<ICloudService, CloudService>();
        services.AddHostedService<InitCloudJob>();
        return services;
    }

    /// <summary>
    /// Ensures the endpoint has a scheme. Bare hosts default to https://.
    /// Explicit http:// (e.g. local MinIO) is preserved.
    /// </summary>
    internal static string NormalizeEndpoint(string endpoint)
    {
        string trimmed = endpoint.Trim().TrimEnd('/');
        if (trimmed.StartsWith("http://", StringComparison.OrdinalIgnoreCase)
            || trimmed.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
        {
            return trimmed;
        }

        return $"https://{trimmed}";
    }
}
