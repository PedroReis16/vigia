using System.Net;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Vigia.Fiware.Config;
using Vigia.Fiware.Contracts;
using Vigia.Fiware.Models.DeviceDTOs;
using Vigia.Fiware.Models.RegistrationDTOs;
using Vigia.Fiware.Models.ServiceDTOs;

namespace Vigia.Fiware.Services;

internal class FiwareService : IFiwareService
{
    private const int DevicesPageSize = 100;

    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly string _iotAgentPath;
    private readonly string _sthCommetPath;
    private readonly string _orionPath;
    private readonly string _iotAgentFullPath;

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

        _iotAgentFullPath = $"{httpClient.BaseAddress}{_iotAgentPath}";
    }

    #region Métodos de controle do serviço do FIWARE
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
    #endregion

    #region Métodos de sincronização de devices
    public async Task<bool> SyncDevicesSchemaAsync()
    {
        List<DeviceAttributeDTO> expectedAttributes = DeviceProperties.GetCameraAttributes();
        List<DeviceCommandDTO> expectedCommands = DeviceProperties.GetCameraCommands();
        List<OrionRegistrationDTO> registrationsCache = await ListRegistrationsAsync();

        bool allSucceeded = true;
        int offset = 0;

        while (true)
        {
            (List<IotAgentDeviceDTO> devices, int totalCount) = await ListDevicesPageAsync(offset, DevicesPageSize);

            if (devices.Count == 0)
                break;

            foreach (IotAgentDeviceDTO device in devices)
            {
                bool schemaMatches = SchemasMatch(device.Attributes, expectedAttributes)
                    && SchemasMatch(device.Commands, expectedCommands);

                if (!schemaMatches)
                {
                    bool updated = await UpdateDeviceSchemaAsync(device.DeviceId, expectedAttributes, expectedCommands);
                    if (!updated)
                    {
                        allSucceeded = false;
                        continue;
                    }
                }

                bool registrationSynced = await SyncCommandRegistrationAsync(
                    device.EntityName,
                    device.EntityType,
                    expectedCommands,
                    registrationsCache);

                if (!registrationSynced)
                    allSucceeded = false;
            }

            offset += devices.Count;

            if (devices.Count < DevicesPageSize || offset >= totalCount)
                break;
        }

        return allSucceeded;
    }

    private async Task<(List<IotAgentDeviceDTO> Devices, int TotalCount)> ListDevicesPageAsync(int offset, int limit)
    {
        string url =
            $"{_iotAgentPath}/devices" +
            $"?limit={limit}&offset={offset}";

        HttpResponseMessage response = await _httpClient.GetAsync(url);

        if (response.StatusCode == HttpStatusCode.NotFound)
            return ([], 0);

        response.EnsureSuccessStatusCode();

        string responseContent = await response.Content.ReadAsStringAsync();
        IotAgentDevicesResponseDTO? payload = JsonSerializer.Deserialize<IotAgentDevicesResponseDTO>(
            responseContent,
            JsonOptions);

        if (payload?.Devices is null || payload.Devices.Count == 0)
            return ([], payload?.Count ?? 0);

        return (payload.Devices, payload.Count);
    }

    private async Task<bool> UpdateDeviceSchemaAsync(
        string deviceId,
        List<DeviceAttributeDTO> attributes,
        List<DeviceCommandDTO> commands)
    {
        UpdateDeviceSchemaDTO body = new()
        {
            Attributes = attributes,
            Commands = commands
        };

        using StringContent content = new(
            JsonSerializer.Serialize(body, JsonOptions),
            Encoding.UTF8,
            "application/json");

        HttpResponseMessage response = await _httpClient.PutAsync(
            $"{_iotAgentPath}/devices/{Uri.EscapeDataString(deviceId)}",
            content);

        return response.IsSuccessStatusCode;
    }

    private static bool SchemasMatch(
        IEnumerable<DeviceAttributeDTO> current,
        IEnumerable<DeviceAttributeDTO> expected)
    {
        HashSet<string> currentKeys = current
            .Select(a => $"{a.ObjectId}|{a.Name}|{a.Type}")
            .ToHashSet(StringComparer.Ordinal);

        HashSet<string> expectedKeys = expected
            .Select(a => $"{a.ObjectId}|{a.Name}|{a.Type}")
            .ToHashSet(StringComparer.Ordinal);

        return currentKeys.SetEquals(expectedKeys);
    }

    private static bool SchemasMatch(
        IEnumerable<DeviceCommandDTO> current,
        IEnumerable<DeviceCommandDTO> expected)
    {
        HashSet<string> currentKeys = current
            .Select(c => $"{c.Name}|{c.Type}")
            .ToHashSet(StringComparer.Ordinal);

        HashSet<string> expectedKeys = expected
            .Select(c => $"{c.Name}|{c.Type}")
            .ToHashSet(StringComparer.Ordinal);

        return currentKeys.SetEquals(expectedKeys);
    }
    #endregion

    #region Métodos de sincronização de registrations (comandos)
    private async Task<bool> SyncCommandRegistrationAsync(
        string entityName,
        string entityType,
        IReadOnlyCollection<DeviceCommandDTO> commands,
        List<OrionRegistrationDTO>? registrationsCache = null)
    {
        List<string> expectedAttrs = commands
            .Select(c => c.Name)
            .Where(name => !string.IsNullOrWhiteSpace(name))
            .Distinct(StringComparer.Ordinal)
            .OrderBy(name => name, StringComparer.Ordinal)
            .ToList();

        List<OrionRegistrationDTO> registrations = registrationsCache ?? await ListRegistrationsAsync();
        List<OrionRegistrationDTO> entityRegistrations = registrations
            .Where(r => IsCommandRegistrationForEntity(r, entityName, entityType))
            .ToList();

        if (expectedAttrs.Count == 0)
        {
            bool deletedAll = true;
            foreach (OrionRegistrationDTO registration in entityRegistrations)
            {
                if (!await DeleteRegistrationAsync(registration.Id))
                {
                    deletedAll = false;
                    continue;
                }

                registrations.RemoveAll(r => r.Id == registration.Id);
            }

            return deletedAll;
        }

        OrionRegistrationDTO? matchingRegistration = entityRegistrations.FirstOrDefault(r =>
            AttrsMatch(r.DataProvided.Attrs, expectedAttrs));

        if (matchingRegistration is not null)
        {
            foreach (OrionRegistrationDTO registration in entityRegistrations.Where(r => r.Id != matchingRegistration.Id))
            {
                if (await DeleteRegistrationAsync(registration.Id))
                    registrations.RemoveAll(r => r.Id == registration.Id);
            }

            return true;
        }

        foreach (OrionRegistrationDTO registration in entityRegistrations)
        {
            if (await DeleteRegistrationAsync(registration.Id))
                registrations.RemoveAll(r => r.Id == registration.Id);
        }

        (bool created, OrionRegistrationDTO? createdRegistration) =
            await CreateCommandRegistrationAsync(entityName, entityType, expectedAttrs);

        if (created && createdRegistration is not null)
            registrations.Add(createdRegistration);

        return created;
    }

    private bool IsCommandRegistrationForEntity(
        OrionRegistrationDTO registration,
        string entityName,
        string entityType)
    {
        bool providerMatches = string.Equals(
            registration.Provider.Http.Url.TrimEnd('/'),
            _iotAgentFullPath.TrimEnd('/'),
            StringComparison.OrdinalIgnoreCase);

        if (!providerMatches)
            return false;

        return registration.DataProvided.Entities.Any(entity =>
            string.Equals(entity.Id, entityName, StringComparison.Ordinal)
            && string.Equals(entity.Type, entityType, StringComparison.Ordinal));
    }

    private static bool AttrsMatch(IEnumerable<string> current, IEnumerable<string> expected)
    {
        HashSet<string> currentAttrs = current.ToHashSet(StringComparer.Ordinal);
        HashSet<string> expectedAttrs = expected.ToHashSet(StringComparer.Ordinal);
        return currentAttrs.SetEquals(expectedAttrs);
    }

    private async Task<List<OrionRegistrationDTO>> ListRegistrationsAsync()
    {
        HttpResponseMessage response = await _httpClient.GetAsync($"{_orionPath}/v2/registrations");

        if (response.StatusCode == HttpStatusCode.NotFound)
            return [];

        response.EnsureSuccessStatusCode();

        string responseContent = await response.Content.ReadAsStringAsync();
        if (string.IsNullOrWhiteSpace(responseContent) || responseContent == "[]")
            return [];

        List<OrionRegistrationDTO>? registrations = JsonSerializer.Deserialize<List<OrionRegistrationDTO>>(
            responseContent,
            JsonOptions);

        return registrations ?? [];
    }

    private async Task<(bool Success, OrionRegistrationDTO? Registration)> CreateCommandRegistrationAsync(
        string entityName,
        string entityType,
        List<string> commandAttrs)
    {
        NewOrionRegistrationDTO body = new()
        {
            Description = $"{entityType} Commands",
            DataProvided = new OrionRegistrationDataProvidedDTO
            {
                Entities =
                [
                    new OrionRegistrationEntityDTO
                    {
                        Id = entityName,
                        Type = entityType
                    }
                ],
                Attrs = commandAttrs
            },
            Provider = new OrionRegistrationProviderDTO
            {
                Http = new OrionRegistrationHttpProviderDTO
                {
                    Url = _iotAgentFullPath
                },
                LegacyForwarding = true
            }
        };

        using StringContent content = new(
            JsonSerializer.Serialize(body, JsonOptions),
            Encoding.UTF8,
            "application/json");

        HttpResponseMessage response = await _httpClient.PostAsync($"{_orionPath}/v2/registrations", content);
        bool success = response.IsSuccessStatusCode || response.StatusCode == HttpStatusCode.Created;
        if (!success)
            return (false, null);

        string? registrationId = null;
        if (response.Headers.Location is not null)
            registrationId = response.Headers.Location.Segments.LastOrDefault()?.TrimEnd('/');

        OrionRegistrationDTO createdRegistration = new()
        {
            Id = registrationId ?? string.Empty,
            Description = body.Description,
            DataProvided = body.DataProvided,
            Provider = body.Provider
        };

        return (true, createdRegistration);
    }

    private async Task<bool> DeleteRegistrationAsync(string registrationId)
    {
        if (string.IsNullOrWhiteSpace(registrationId))
            return false;

        HttpResponseMessage response = await _httpClient.DeleteAsync(
            $"{_orionPath}/v2/registrations/{Uri.EscapeDataString(registrationId)}");

        return response.IsSuccessStatusCode || response.StatusCode == HttpStatusCode.NoContent;
    }
    #endregion


    public async Task<bool> RegisterSensorAsync(Guid deviceId, string deviceName)
    {
        string entityType = _configuration.GetValue<string>("Fiware:Services:EntityType")!;
        string entityName = $"urn:ngsi-ld:{deviceName}";

        List<DeviceAttributeDTO> attributes = DeviceProperties.GetCameraAttributes();
        List<DeviceCommandDTO> commands = DeviceProperties.GetCameraCommands();

        NewDevicesRequestDTO body = new()
        {
            Devices =
            [
                new NewDeviceDTO
                {
                    DeviceId = deviceId,
                    EntityName = entityName,
                    EntityType = entityType,
                    Protocol = DeviceProperties.Protocol,
                    Transport = DeviceProperties.Transport,
                    Attributes = attributes,
                    Commands = commands
                }
            ]
        };

        using StringContent content = new(
            JsonSerializer.Serialize(body, JsonOptions),
            Encoding.UTF8,
            "application/json");

        HttpResponseMessage response = await _httpClient.PostAsync($"{_iotAgentPath}/devices", content);
        if (!response.IsSuccessStatusCode)
            return false;

        return await SyncCommandRegistrationAsync(entityName, entityType, commands);
    }

    public async Task DeleteSensorAsync(Guid deviceId, string deviceName)
    {
        Task deleteIotAgentTask = DeleteDeviceFromIotAgentAsync(deviceId);
        Task deleteOrionTask = DeleteDeviceFromOrionAsync(deviceName);

        await Task.WhenAll(deleteIotAgentTask, deleteOrionTask);
    }

    private async Task DeleteDeviceFromIotAgentAsync(Guid deviceId)
    {
        HttpResponseMessage response = await _httpClient.DeleteAsync(
            $"{_iotAgentPath}/devices/{deviceId}");

        response.EnsureSuccessStatusCode();
    }

    private async Task DeleteDeviceFromOrionAsync(string deviceName)
    {
        string entityName = $"urn:ngsi-ld:{deviceName}";

        HttpResponseMessage response = await _httpClient.DeleteAsync(
            $"{_orionPath}/v2/entities/{entityName}");

        response.EnsureSuccessStatusCode();
    }
}
