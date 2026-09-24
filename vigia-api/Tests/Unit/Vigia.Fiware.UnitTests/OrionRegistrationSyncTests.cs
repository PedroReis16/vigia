using Vigia.Fiware.Models.RegistrationDTOs;
using Vigia.Fiware.Services;

namespace Vigia.Fiware.UnitTests;

public class OrionRegistrationSyncTests
{
    [Fact]
    public void ResolveProviderUrl_UsaConfigQuandoInformada()
    {
        string result = OrionRegistrationSync.ResolveProviderUrl(" http://iot-agent:4041/ ");

        Assert.Equal("http://iot-agent:4041", result);
    }

    [Fact]
    public void ResolveProviderUrl_SemConfig_UsaNorteNgsiPadrao()
    {
        Assert.Equal(
            OrionRegistrationSync.DefaultProviderUrl,
            OrionRegistrationSync.ResolveProviderUrl(null));
        Assert.Equal(
            OrionRegistrationSync.DefaultProviderUrl,
            OrionRegistrationSync.ResolveProviderUrl("   "));
    }

    [Fact]
    public void ResolveProviderUrl_NaoUsaPathAdminDoTraefik()
    {
        string result = OrionRegistrationSync.ResolveProviderUrl(null);

        Assert.DoesNotContain("/vigia/fiware/iot", result, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("host.docker.internal", result, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void FindCanonical_IgnoraRegistrationComUrlAdminDoTraefik()
    {
        const string entityName = "urn:ngsi-ld:Vigia-a1b2c3d4";
        const string entityType = "Sensor";
        string[] attrs = ["device_off", "device_on", "device_update", "stream_off", "stream_on"];

        OrionRegistrationDTO traefik = Registration(
            "bad",
            entityName,
            entityType,
            "http://host.docker.internal:81/vigia/fiware/iot",
            attrs);
        OrionRegistrationDTO canonical = Registration(
            "ok",
            entityName,
            entityType,
            "http://iot-agent:4041",
            attrs);

        OrionRegistrationDTO? found = OrionRegistrationSync.FindCanonical(
            [traefik, canonical],
            entityName,
            entityType,
            "http://iot-agent:4041",
            attrs);

        Assert.NotNull(found);
        Assert.Equal("ok", found.Id);
    }

    [Fact]
    public void FindCanonical_ExigeMesmosAtributosDeComando()
    {
        const string entityName = "urn:ngsi-ld:Vigia-a1b2c3d4";
        OrionRegistrationDTO incomplete = Registration(
            "incomplete",
            entityName,
            "Sensor",
            "http://iot-agent:4041",
            ["stream_on"]);

        OrionRegistrationDTO? found = OrionRegistrationSync.FindCanonical(
            [incomplete],
            entityName,
            "Sensor",
            "http://iot-agent:4041",
            ["stream_on", "stream_off"]);

        Assert.Null(found);
    }

    [Fact]
    public void IsForEntity_NaoExigeUrlDoProvider()
    {
        OrionRegistrationDTO registration = Registration(
            "any",
            "urn:ngsi-ld:Vigia-a1b2c3d4",
            "Sensor",
            "http://localhost:81/vigia/fiware/iot",
            ["stream_on"]);

        Assert.True(OrionRegistrationSync.IsForEntity(
            registration,
            "urn:ngsi-ld:Vigia-a1b2c3d4",
            "Sensor"));
    }

    private static OrionRegistrationDTO Registration(
        string id,
        string entityName,
        string entityType,
        string providerUrl,
        IEnumerable<string> attrs) =>
        new()
        {
            Id = id,
            DataProvided = new OrionRegistrationDataProvidedDTO
            {
                Entities =
                [
                    new OrionRegistrationEntityDTO { Id = entityName, Type = entityType }
                ],
                Attrs = [.. attrs]
            },
            Provider = new OrionRegistrationProviderDTO
            {
                Http = new OrionRegistrationHttpProviderDTO { Url = providerUrl }
            }
        };
}
