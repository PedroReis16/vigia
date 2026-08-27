using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Vigia.Fiware.BackgroundJobs;
using Vigia.Fiware.Config;
using Vigia.Fiware.Contracts;
using Vigia.Fiware.Services;
using Vigia.Models.Middlewares;

namespace Vigia.Fiware.Extensions;

public static class FiwareExtension
{
    private const string ApiUrlsSection = "ApiUrls";
    private const string FiwareUrlKey = "Fiware";

    public static IServiceCollection AddFiware(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<DeviceSchemaOptions>(configuration.GetSection(DeviceSchemaOptions.SectionName));
        services.Configure<SubscriptionSchemaOptions>(configuration.GetSection(SubscriptionSchemaOptions.SectionName));

        services.AddHttpClient<IFiwareService, FiwareService>(httpClient =>
        {
            IConfigurationSection apiSection = configuration.GetSection(ApiUrlsSection);

            string service = configuration.GetValue<string>("Fiware:RequestHeaders:Service")!;
            string servicePath = configuration.GetValue<string>("Fiware:RequestHeaders:ServicePath")!;

            httpClient.DefaultRequestHeaders.Add("fiware-service", service);
            httpClient.DefaultRequestHeaders.Add("fiware-servicepath", servicePath);

            httpClient.BaseAddress = new Uri(apiSection.GetValue<string>(FiwareUrlKey)!);
        })
        .AddHttpMessageHandler<ForwardingHandler>();

        services.AddHostedService<FiwareServiceJob>();

        return services;
    }
}
