using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Vigia.Database.Contracts;
using Vigia.Fiware.Config;
using Vigia.Fiware.Contracts;
using Vigia.Fiware.Models.DeviceDTOs;
using Vigia.Fiware.Models.RegistrationDTOs;
using Vigia.Fiware.Models.ServiceDTOs;
using Vigia.Fiware.Models.SubscriptionDTOs;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

#if DEBUG
using Vigia.Models.Seed;
#endif

namespace Vigia.Fiware.Services;

internal class FiwareService : IFiwareService
{
    private const int DevicesPageSize = 100;
    private const int SubscriptionsPageSize = 100;

    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly ILogger<FiwareService> _logger;
    private readonly IFiwarePropertiesDao _fiwarePropertiesDao;
    private readonly DeviceSchemaOptions _deviceSchema;
    private readonly SubscriptionSchemaOptions _subscriptions;
    private readonly string _iotAgentPath;
    private readonly string _orionPath;
    private readonly string _iotAgentProviderUrl;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public FiwareService(
        HttpClient httpClient,
        IConfiguration configuration,
        IOptionsSnapshot<DeviceSchemaOptions> deviceSchemaOptions,
        IOptionsSnapshot<SubscriptionSchemaOptions> subscriptionOptions,
        IFiwarePropertiesDao fiwarePropertiesDao,
        ILogger<FiwareService> logger)
    {
        _httpClient = httpClient;
        _configuration = configuration;
        _logger = logger;
        _fiwarePropertiesDao = fiwarePropertiesDao;
        _deviceSchema = deviceSchemaOptions.Value;
        _subscriptions = subscriptionOptions.Value;
        _iotAgentPath = configuration.GetValue<string>("Fiware:Paths:IotAgent")!;
        _orionPath = configuration.GetValue<string>("Fiware:Paths:Orion")!;
        _iotAgentProviderUrl = $"{httpClient.BaseAddress}{_iotAgentPath}";
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
        List<DeviceAttributeDTO> expectedAttributes = _deviceSchema.GetAttributes();
        List<DeviceCommandDTO> expectedCommands = _deviceSchema.GetCommands();
        string expectedProtocol = _deviceSchema.Protocol;
        string expectedTransport = _deviceSchema.Transport;

        FiwareProperties? savedProperties = (await _fiwarePropertiesDao.AllAsync()).FirstOrDefault();

        if (savedProperties is not null
            && PropertiesMatch(savedProperties, expectedProtocol, expectedTransport, expectedAttributes, expectedCommands))
        {
            _logger.LogInformation(
                "Schema FIWARE já sincronizado com FiwareProperties. Nenhuma atualização necessária.");
            return true;
        }

        _logger.LogInformation(
            "Schema FIWARE divergente de FiwareProperties. Attributes=[{Attributes}] Commands=[{Commands}]. Iniciando varredura...",
            string.Join(", ", expectedAttributes.Select(a => a.Name)),
            string.Join(", ", expectedCommands.Select(c => c.Name)));

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
                    && SchemasMatch(device.Commands, expectedCommands)
                    && string.Equals(device.Protocol ?? expectedProtocol, expectedProtocol, StringComparison.Ordinal)
                    && string.Equals(device.Transport ?? expectedTransport, expectedTransport, StringComparison.Ordinal);

                if (schemaMatches)
                    continue;

                _logger.LogInformation(
                    "Device {DeviceId} desatualizado. Atualizando via PUT...",
                    device.DeviceId);

                bool updated = await UpdateDeviceAsync(
                    device,
                    expectedProtocol,
                    expectedTransport,
                    expectedAttributes,
                    expectedCommands);

                if (!updated)
                    allSucceeded = false;
            }

            offset += devices.Count;

            if (devices.Count < DevicesPageSize || offset >= totalCount)
                break;
        }

        if (!allSucceeded)
            return false;

        await PersistFiwarePropertiesAsync(
            savedProperties,
            expectedProtocol,
            expectedTransport,
            expectedAttributes,
            expectedCommands);

        _logger.LogInformation("FiwareProperties atualizado com o schema de Fiware:Devices.");
        return true;
    }

    public async Task<(List<IotAgentDeviceDTO> Devices, int TotalCount)> ListDevicesPageAsync(int offset, int limit)
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

    private async Task<bool> UpdateDeviceAsync(
        IotAgentDeviceDTO device,
        string protocol,
        string transport,
        List<DeviceAttributeDTO> attributes,
        List<DeviceCommandDTO> commands)
    {
        UpdateDeviceDTO body = new()
        {
            EntityName = device.EntityName,
            EntityType = device.EntityType,
            Protocol = protocol,
            Transport = transport,
            Attributes = attributes,
            Commands = commands
        };

        using StringContent content = new(
            JsonSerializer.Serialize(body, JsonOptions),
            Encoding.UTF8,
            "application/json");

        HttpResponseMessage response = await _httpClient.PutAsync(
            $"{_iotAgentPath}/devices/{Uri.EscapeDataString(device.DeviceId)}",
            content);

        if (response.IsSuccessStatusCode || response.StatusCode == HttpStatusCode.NoContent)
            return true;

        string errorBody = await response.Content.ReadAsStringAsync();
        _logger.LogError(
            "Falha ao atualizar device {DeviceId}. Status={StatusCode}. Body={Body}",
            device.DeviceId,
            (int)response.StatusCode,
            errorBody);

        return false;
    }

    private async Task PersistFiwarePropertiesAsync(
        FiwareProperties? existing,
        string protocol,
        string transport,
        List<DeviceAttributeDTO> attributes,
        List<DeviceCommandDTO> commands)
    {
        List<SensorAttribute> sensorAttributes = attributes
            .Select(a => new SensorAttribute
            {
                ObjectId = a.ObjectId,
                Name = a.Name,
                Type = a.Type
            })
            .ToList();

        List<SensorCommand> sensorCommands = commands
            .Select(c => new SensorCommand
            {
                Name = c.Name,
                Type = c.Type
            })
            .ToList();

        if (existing is null)
        {
            await _fiwarePropertiesDao.AddAsync(new FiwareProperties
            {
                Protocol = protocol,
                Transport = transport,
                Attributes = sensorAttributes,
                Commands = sensorCommands
            });
            return;
        }

        existing.Protocol = protocol;
        existing.Transport = transport;
        existing.Attributes = sensorAttributes;
        existing.Commands = sensorCommands;

        await _fiwarePropertiesDao.UpdateAsync(existing);
    }

    private static bool PropertiesMatch(
        FiwareProperties saved,
        string protocol,
        string transport,
        IEnumerable<DeviceAttributeDTO> attributes,
        IEnumerable<DeviceCommandDTO> commands)
    {
        if (!string.Equals(saved.Protocol, protocol, StringComparison.Ordinal)
            || !string.Equals(saved.Transport, transport, StringComparison.Ordinal))
        {
            return false;
        }

        return SchemasMatch(
                saved.Attributes.Select(a => new DeviceAttributeDTO
                {
                    ObjectId = a.ObjectId,
                    Name = a.Name,
                    Type = a.Type
                }),
                attributes)
            && SchemasMatch(
                saved.Commands.Select(c => new DeviceCommandDTO
                {
                    Name = c.Name,
                    Type = c.Type
                }),
                commands);
    }

    private static bool SchemasMatch(
        IEnumerable<DeviceAttributeDTO> current,
        IEnumerable<DeviceAttributeDTO> expected)
    {
        List<string> currentKeys = current
            .Select(a => $"{a.ObjectId}|{a.Name}|{a.Type}")
            .OrderBy(key => key, StringComparer.Ordinal)
            .ToList();

        List<string> expectedKeys = expected
            .Select(a => $"{a.ObjectId}|{a.Name}|{a.Type}")
            .OrderBy(key => key, StringComparer.Ordinal)
            .ToList();

        return currentKeys.SequenceEqual(expectedKeys, StringComparer.Ordinal);
    }

    private static bool SchemasMatch(
        IEnumerable<DeviceCommandDTO> current,
        IEnumerable<DeviceCommandDTO> expected)
    {
        List<string> currentKeys = current
            .Select(c => $"{c.Name}|{c.Type}")
            .OrderBy(key => key, StringComparer.Ordinal)
            .ToList();

        List<string> expectedKeys = expected
            .Select(c => $"{c.Name}|{c.Type}")
            .OrderBy(key => key, StringComparer.Ordinal)
            .ToList();

        return currentKeys.SequenceEqual(expectedKeys, StringComparer.Ordinal);
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
            _iotAgentProviderUrl.TrimEnd('/'),
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
                    Url = _iotAgentProviderUrl
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
        // if (response.Headers.Location is not null)
        //     registrationId = response.Headers.Location.Segments.LastOrDefault()?.TrimEnd('/');

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

    #region Métodos de sincronização de subscriptions
    public async Task<bool> SyncSubscriptionsAsync()
    {
        List<SubscriptionDefinitionOptions> definitions = _subscriptions.GetSubscriptions();
        string entityType = _configuration.GetValue<string>("Fiware:Services:EntityType")!;
        List<OrionSubscriptionDTO> subscriptions = await ListSubscriptionsAsync();

        if (definitions.Count == 0)
        {
            _logger.LogInformation("Nenhuma subscrição configurada em Fiware:Subscriptions.");
            return true;
        }

        _logger.LogInformation(
            "Sincronizando {Count} subscrição(ões) Orion a partir de Fiware:Subscriptions",
            definitions.Count);

        bool allSucceeded = true;
        int offset = 0;

        while (true)
        {
            (List<IotAgentDeviceDTO> devices, int totalCount) = await ListDevicesPageAsync(offset, DevicesPageSize);

            if (devices.Count == 0)
                break;

            foreach (IotAgentDeviceDTO device in devices)
            {
                if (string.IsNullOrWhiteSpace(device.EntityName))
                    continue;

                string deviceEntityType = string.IsNullOrWhiteSpace(device.EntityType)
                    ? entityType
                    : device.EntityType;

                if (!await SyncDeviceSubscriptionsAsync(
                    device.EntityName,
                    deviceEntityType,
                    definitions,
                    subscriptions))
                {
                    allSucceeded = false;
                }
            }

            offset += devices.Count;

            if (devices.Count < DevicesPageSize || offset >= totalCount)
                break;
        }

        return allSucceeded;
    }

    private async Task<bool> SyncDeviceSubscriptionsAsync(
        string entityName,
        string entityType,
        IReadOnlyCollection<SubscriptionDefinitionOptions>? definitions = null,
        List<OrionSubscriptionDTO>? subscriptionsCache = null)
    {
        List<SubscriptionDefinitionOptions> expected = (definitions ?? _subscriptions.GetSubscriptions()).ToList();
        List<OrionSubscriptionDTO> subscriptions = subscriptionsCache ?? await ListSubscriptionsAsync();

        bool allSucceeded = true;

        foreach (SubscriptionDefinitionOptions definition in expected)
        {
            List<OrionSubscriptionDTO> urlSubscriptions = subscriptions
                .Where(s => IsSubscriptionForEntity(s, entityName, entityType)
                    && UrlsMatch(s.Notification.Http.Url, definition.Notification.Url))
                .ToList();

            OrionSubscriptionDTO? matching = urlSubscriptions.FirstOrDefault(s =>
                MatchesDefinition(s, definition));

            if (matching is not null)
            {
                foreach (OrionSubscriptionDTO duplicate in urlSubscriptions.Where(s => s.Id != matching.Id))
                {
                    if (!await DeleteSubscriptionAsync(duplicate.Id))
                    {
                        allSucceeded = false;
                        continue;
                    }

                    subscriptions.RemoveAll(s => s.Id == duplicate.Id);
                }

                continue;
            }

            foreach (OrionSubscriptionDTO outdated in urlSubscriptions)
            {
                if (await DeleteSubscriptionAsync(outdated.Id))
                    subscriptions.RemoveAll(s => s.Id == outdated.Id);
                else
                    allSucceeded = false;
            }

            (bool created, OrionSubscriptionDTO? createdSubscription) =
                await CreateSubscriptionAsync(entityName, entityType, definition);

            if (created && createdSubscription is not null)
                subscriptions.Add(createdSubscription);
            else
                allSucceeded = false;
        }

        return allSucceeded;
    }

    private static bool MatchesDefinition(
        OrionSubscriptionDTO subscription,
        SubscriptionDefinitionOptions definition)
    {
        bool urlMatches = UrlsMatch(subscription.Notification.Http.Url, definition.Notification.Url);
        bool conditionAttrsMatch = AttrsMatch(subscription.Subject.Condition.Attrs, definition.GetConditionAttrs());
        bool notificationAttrsMatch = AttrsMatch(subscription.Notification.Attrs, definition.GetNotificationAttrs());
        bool queryMatches = string.Equals(
            subscription.Subject.Condition.Expression?.Q?.Trim(),
            definition.GetExpression(),
            StringComparison.Ordinal);
        string expectedFormat = definition.GetAttrsFormat();
        bool formatMatches = string.IsNullOrWhiteSpace(subscription.Notification.AttrsFormat)
            || string.Equals(
                subscription.Notification.AttrsFormat,
                expectedFormat,
                StringComparison.OrdinalIgnoreCase);

        return urlMatches && conditionAttrsMatch && notificationAttrsMatch && queryMatches && formatMatches;
    }

    private static bool IsSubscriptionForEntity(
        OrionSubscriptionDTO subscription,
        string entityName,
        string entityType) =>
        subscription.Subject.Entities.Any(entity =>
            string.Equals(entity.Id, entityName, StringComparison.Ordinal)
            && string.Equals(entity.Type, entityType, StringComparison.Ordinal));

    private static bool UrlsMatch(string current, string expected)
    {
        if (string.IsNullOrWhiteSpace(current) || string.IsNullOrWhiteSpace(expected))
            return false;

        return string.Equals(
            current.TrimEnd('/'),
            expected.TrimEnd('/'),
            StringComparison.OrdinalIgnoreCase);
    }

    private async Task<List<OrionSubscriptionDTO>> ListSubscriptionsAsync()
    {
        List<OrionSubscriptionDTO> subscriptions = [];
        int offset = 0;

        while (true)
        {
            string url =
                $"{_orionPath}/v2/subscriptions" +
                $"?limit={SubscriptionsPageSize}&offset={offset}";

            HttpResponseMessage response = await _httpClient.GetAsync(url);

            if (response.StatusCode == HttpStatusCode.NotFound)
                return subscriptions;

            response.EnsureSuccessStatusCode();

            string responseContent = await response.Content.ReadAsStringAsync();
            if (string.IsNullOrWhiteSpace(responseContent) || responseContent == "[]")
                break;

            List<OrionSubscriptionDTO>? page = JsonSerializer.Deserialize<List<OrionSubscriptionDTO>>(
                responseContent,
                JsonOptions);

            if (page is null || page.Count == 0)
                break;

            subscriptions.AddRange(page);
            offset += page.Count;

            if (page.Count < SubscriptionsPageSize)
                break;
        }

        return subscriptions;
    }

    private async Task<(bool Success, OrionSubscriptionDTO? Subscription)> CreateSubscriptionAsync(
        string entityName,
        string entityType,
        SubscriptionDefinitionOptions definition)
    {
        List<string> conditionAttrs = definition.GetConditionAttrs();
        List<string> notificationAttrs = definition.GetNotificationAttrs();
        string? expression = definition.GetExpression();

        NewOrionSubscriptionDTO body = new()
        {
            Description = definition.FormatDescription(entityName, entityType),
            Subject = new OrionSubscriptionSubjectDTO
            {
                Entities =
                [
                    new OrionRegistrationEntityDTO
                    {
                        Id = entityName,
                        Type = entityType
                    }
                ],
                Condition = new OrionSubscriptionConditionDTO
                {
                    Attrs = conditionAttrs,
                    Expression = expression is null
                        ? null
                        : new OrionSubscriptionExpressionDTO
                        {
                            Q = expression
                        }
                }
            },
            Notification = new OrionSubscriptionNotificationDTO
            {
                Http = new OrionSubscriptionHttpDTO
                {
                    Url = definition.Notification.Url.TrimEnd('/')
                },
                Attrs = notificationAttrs,
                AttrsFormat = definition.GetAttrsFormat()
            }
        };

        using StringContent content = new(
            JsonSerializer.Serialize(body, JsonOptions),
            Encoding.UTF8,
            "application/json");

        HttpResponseMessage response = await _httpClient.PostAsync($"{_orionPath}/v2/subscriptions", content);
        bool success = response.IsSuccessStatusCode || response.StatusCode == HttpStatusCode.Created;
        if (!success)
        {
            string errorBody = await response.Content.ReadAsStringAsync();
            _logger.LogError(
                "Falha ao criar subscrição para {EntityName} ({Description}). Status={StatusCode}. Body={Body}",
                entityName,
                body.Description,
                (int)response.StatusCode,
                errorBody);
            return (false, null);
        }

        string? subscriptionId = TryGetIdFromLocation(response.Headers.Location);

        OrionSubscriptionDTO createdSubscription = new()
        {
            Id = subscriptionId ?? string.Empty,
            Description = body.Description,
            Subject = body.Subject,
            Notification = body.Notification
        };

        _logger.LogInformation(
            "Subscrição criada para {EntityName} ({SubscriptionId}): {Description}",
            entityName,
            createdSubscription.Id,
            body.Description);

        return (true, createdSubscription);
    }

    private static string? TryGetIdFromLocation(Uri? location)
    {
        if (location is null)
            return null;

        // Orion pode devolver Location relativa; Uri.Segments lança em relative URIs.
        string path = location.IsAbsoluteUri ? location.AbsolutePath : location.OriginalString;
        string? last = path.Split('/', StringSplitOptions.RemoveEmptyEntries).LastOrDefault();
        return string.IsNullOrWhiteSpace(last) ? null : last.TrimEnd('/');
    }

    private async Task<bool> DeleteSubscriptionAsync(string subscriptionId)
    {
        if (string.IsNullOrWhiteSpace(subscriptionId))
            return false;

        HttpResponseMessage response = await _httpClient.DeleteAsync(
            $"{_orionPath}/v2/subscriptions/{Uri.EscapeDataString(subscriptionId)}");

        return response.IsSuccessStatusCode
            || response.StatusCode == HttpStatusCode.NoContent
            || response.StatusCode == HttpStatusCode.NotFound;
    }

    private async Task DeleteManagedSubscriptionsAsync(string entityName, string entityType)
    {
        HashSet<string> managedUrls = _subscriptions.GetSubscriptions()
            .Select(definition => definition.Notification.Url.TrimEnd('/'))
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        if (managedUrls.Count == 0)
            return;

        List<OrionSubscriptionDTO> subscriptions = await ListSubscriptionsAsync();
        foreach (OrionSubscriptionDTO subscription in subscriptions.Where(s =>
            IsSubscriptionForEntity(s, entityName, entityType)
            && managedUrls.Contains(s.Notification.Http.Url.TrimEnd('/'))))
        {
            await DeleteSubscriptionAsync(subscription.Id);
        }
    }
    #endregion

    public async Task<bool> EnsureDevicesProvisionedAsync(
        IReadOnlyCollection<(Guid DeviceId, string DeviceName)> devices)
    {
        if (devices.Count == 0)
            return true;

        HashSet<string> provisionedIds = await ListAllProvisionedDeviceIdsAsync();
        bool allSucceeded = true;

        foreach ((Guid deviceId, string deviceName) in devices)
        {
            if (provisionedIds.Contains(deviceId.ToString()))
                continue;

            _logger.LogWarning(
                "Device {DeviceId} ({DeviceName}) presente no banco e ausente no FIWARE. Provisionando...",
                deviceId,
                deviceName);

            if (!await RegisterSensorAsync(deviceId, deviceName))
                allSucceeded = false;
        }

        return allSucceeded;
    }

    private async Task<HashSet<string>> ListAllProvisionedDeviceIdsAsync()
    {
        HashSet<string> ids = new(StringComparer.OrdinalIgnoreCase);
        int offset = 0;

        while (true)
        {
            (List<IotAgentDeviceDTO> page, int totalCount) =
                await ListDevicesPageAsync(offset, DevicesPageSize);

            foreach (IotAgentDeviceDTO device in page)
            {
                if (!string.IsNullOrWhiteSpace(device.DeviceId))
                    ids.Add(device.DeviceId);
            }

            offset += page.Count;

            if (page.Count == 0 || page.Count < DevicesPageSize || offset >= totalCount)
                break;
        }

        return ids;
    }

#if DEBUG
    public async Task<bool> EnsureSeedDeviceAsync() =>
        await RegisterSensorAsync(TestDeviceSeed.Id, TestDeviceSeed.Name);
#endif

    public async Task<bool> RegisterSensorAsync(Guid deviceId, string deviceName)
    {
        string entityType = _configuration.GetValue<string>("Fiware:Services:EntityType")!;
        string entityName = $"urn:ngsi-ld:{deviceName}";
        List<DeviceAttributeDTO> attributes = _deviceSchema.GetAttributes();
        List<DeviceCommandDTO> commands = _deviceSchema.GetCommands();

        HttpResponseMessage existing = await _httpClient.GetAsync(
            $"{_iotAgentPath}/devices/{Uri.EscapeDataString(deviceId.ToString())}");

        if (existing.IsSuccessStatusCode)
        {
            _logger.LogInformation(
                "Device {DeviceId} ({DeviceName}) já provisionado no FIWARE. Sincronizando registration/subscrições...",
                deviceId,
                deviceName);

            return await SyncCommandRegistrationAsync(entityName, entityType, commands)
                && await SyncDeviceSubscriptionsAsync(entityName, entityType);
        }

        if (existing.StatusCode != HttpStatusCode.NotFound)
        {
            string errorBody = await existing.Content.ReadAsStringAsync();
            _logger.LogError(
                "Falha ao consultar device {DeviceId}. Status={StatusCode}. Body={Body}",
                deviceId,
                (int)existing.StatusCode,
                errorBody);
            return false;
        }

        _logger.LogInformation(
            "Provisionando device {DeviceId} no IoT Agent com Attributes=[{Attributes}] Commands=[{Commands}]",
            deviceId,
            string.Join(", ", attributes.Select(a => a.Name)),
            string.Join(", ", commands.Select(c => c.Name)));

        NewDevicesRequestDTO body = new()
        {
            Devices =
            [
                new NewDeviceDTO
                {
                    DeviceId = deviceId.ToString(),
                    EntityName = entityName,
                    EntityType = entityType,
                    Protocol = _deviceSchema.Protocol,
                    Transport = _deviceSchema.Transport,
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
        if (!response.IsSuccessStatusCode && response.StatusCode != HttpStatusCode.Created)
        {
            string errorBody = await response.Content.ReadAsStringAsync();
            _logger.LogError(
                "Falha ao provisionar device {DeviceId}. Status={StatusCode}. Body={Body}",
                deviceId,
                (int)response.StatusCode,
                errorBody);
            return false;
        }

        return await SyncCommandRegistrationAsync(entityName, entityType, commands)
            && await SyncDeviceSubscriptionsAsync(entityName, entityType);
    }

    public async Task DeleteSensorAsync(Guid deviceId, string deviceName)
    {
        string entityName = $"urn:ngsi-ld:{deviceName}";
        string entityType = _configuration.GetValue<string>("Fiware:Services:EntityType")!;
        await DeleteManagedSubscriptionsAsync(entityName, entityType);

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

    public async Task<bool> SendCommandAsync(string deviceName, DeviceCommands command, string? commandValue = null)
    {
        string entityType = _configuration.GetValue<string>("Fiware:Services:EntityType")!;
        string entityName = $"urn:ngsi-ld:{deviceName}";

        string bodyContent =
        $"{{\"{command.GetCommandName()}\": {{\"value\": \"{commandValue ?? string.Empty}\",\"type\": \"command\"}}}}";

        using StringContent content = new(bodyContent, Encoding.UTF8, "application/json");

        HttpResponseMessage response = await _httpClient.PatchAsync(
            $"{_orionPath}/v2/entities/{entityName}/attrs?type={entityType}",
            content);

        if (response.IsSuccessStatusCode)
            return true;

        string errorBody = await response.Content.ReadAsStringAsync();
        _logger.LogError(
            "Falha ao enviar comando {Command} para {EntityName}. Status={StatusCode}. Body={Body}",
            command.GetCommandName(),
            entityName,
            (int)response.StatusCode,
            errorBody);

        return false;
    }
}
