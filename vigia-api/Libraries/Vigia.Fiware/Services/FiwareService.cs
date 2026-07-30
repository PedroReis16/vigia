using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Vigia.Fiware.Contracts;
using Vigia.Fiware.Models;

namespace Vigia.Fiware.Services;

internal class FiwareService : IFiwareService
{
    private readonly HttpClient _httpClient ;
    private readonly IConfiguration _configuration;
    private readonly string _iotAgentPath;
    private readonly string _sthCommetPath;
    private readonly string _orionPath;


    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public FiwareService(HttpClient httpClient, IConfiguration configuration)
    {
        _httpClient = httpClient;
        _configuration = configuration;
        _iotAgentPath = configuration.GetValue<string>("Fiware:Paths:IotAgent")!;
        _sthCommetPath = configuration.GetValue<string>("Fiware:Paths:SthComet")!;
        _orionPath = configuration.GetValue<string>("Fiware:Paths:Orion")!;
    }

    public async Task<bool> AddOrUpdateServiceAsync()
    {
        string apiKey = _configuration.GetValue<string>("Fiware:Services:ApiKey")!;
        string entityType = _configuration.GetValue<string>("Fiware:Services:EntityType")!;
        string resource = _configuration.GetValue<string>("Fiware:Services:Resource")!;

        var serviceRegistered = await FindServiceAsync();

        if (serviceRegistered is null)
            return await CreateServiceAsync(apiKey, entityType, resource);

        var (currentApiKey, currentEntityType, currentResource) = serviceRegistered.Value;

        if (currentApiKey == apiKey
            && currentEntityType == entityType
            && currentResource == resource)
            return true;

        return await UpdateServiceAsync(currentApiKey, currentResource, apiKey, entityType, resource);
    }

    private async Task<(string apiKey, string entityType, string resource)?> FindServiceAsync()
    {
        HttpResponseMessage response = await _httpClient.GetAsync($"{_iotAgentPath}/services");

        response.EnsureSuccessStatusCode();

        string responseContent = await response.Content.ReadAsStringAsync();

        IotAgentServicesResponseDTO? payload = JsonSerializer.Deserialize<IotAgentServicesResponseDTO>(
            responseContent,
            JsonOptions);

        IotAgentServiceDTO? firstService = payload?.Services.FirstOrDefault();
        if (firstService is null)
            return null;

        return (firstService.ApiKey, firstService.EntityType, firstService.Resource);
    }

    private async Task<bool> CreateServiceAsync(string apiKey, string entityType, string resource)
    {
        NewIotServiceDTO body = new()
        {
            Services =
            [
                new IotAgentServicePayloadDTO
                {
                    ApiKey = apiKey,
                    EntityType = entityType,
                    Resource = resource
                }
            ]
        };

        using StringContent content = new(
            JsonSerializer.Serialize(body, JsonOptions),
            Encoding.UTF8,
            "application/json");

        HttpResponseMessage response = await _httpClient.PostAsync($"{_iotAgentPath}/services", content);

        return response.IsSuccessStatusCode;
    }

    private async Task<bool> UpdateServiceAsync(
        string currentApiKey,
        string currentResource,
        string apiKey,
        string entityType,
        string resource)
    {
        string url =
            $"{_iotAgentPath}/services" +
            $"?resource={Uri.EscapeDataString(currentResource)}" +
            $"&apikey={Uri.EscapeDataString(currentApiKey)}";

        IotAgentServicePayloadDTO body = new()
        {
            ApiKey = apiKey,
            EntityType = entityType,
            Resource = resource
        };

        using StringContent content = new(
            JsonSerializer.Serialize(body, JsonOptions),
            Encoding.UTF8,
            "application/json");

        HttpResponseMessage response = await _httpClient.PutAsync(url, content);

        return response.IsSuccessStatusCode;
    }
}
