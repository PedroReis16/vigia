using System.Net;
using System.Text;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Services;

namespace Vigia.API.UnitTests;

public class KeycloakAdminClientTests
{
    [Fact]
    public async Task UpdateProfileAsync_PatchesTheExistingUser()
    {
        Guid userId = Guid.Parse("11111111-1111-1111-1111-111111111111");
        RecordingHandler handler = new();
        handler.Enqueue(HttpStatusCode.OK, """{"access_token":"adm","expires_in":300}""");
        handler.Enqueue(HttpStatusCode.OK, """
            {
              "id": "11111111-1111-1111-1111-111111111111",
              "username": "ana",
              "email": "ana@vigia.test",
              "firstName": "Ana",
              "lastName": "Lima",
              "attributes": { "phone": ["11999990000"], "locale": ["pt-BR"] }
            }
            """);
        handler.Enqueue(HttpStatusCode.NoContent, "");

        KeycloakAdminClient client = CreateClient(handler);

        await client.UpdateProfileAsync(userId, "Ana", "Souza", "11988887777");

        Assert.Equal(3, handler.Calls.Count);
        Assert.EndsWith("/realms/master/protocol/openid-connect/token", handler.Calls[0].Path);
        Assert.Equal(
            $"/auth/admin/realms/vigia/users/{userId:D}",
            handler.Calls[1].Path);
        Assert.Contains("\"firstName\":\"Ana\"", handler.Calls[2].Body);
        Assert.Contains("\"lastName\":\"Souza\"", handler.Calls[2].Body);
        Assert.Contains("\"phone\":[\"11988887777\"]", handler.Calls[2].Body);
        Assert.Contains("\"locale\":[\"pt-BR\"]", handler.Calls[2].Body);
        Assert.Contains("\"email\":\"ana@vigia.test\"", handler.Calls[2].Body);
    }

    [Fact]
    public async Task DeleteUserAsync_TreatsNotFoundAsAlreadyDeleted()
    {
        RecordingHandler handler = new();
        handler.Enqueue(HttpStatusCode.OK, """{"access_token":"adm","expires_in":300}""");
        handler.Enqueue(HttpStatusCode.NotFound, "");

        KeycloakAdminClient client = CreateClient(handler);

        await client.DeleteUserAsync(Guid.NewGuid());

        Assert.Equal(HttpMethod.Delete, handler.Calls[1].Method);
    }

    private static KeycloakAdminClient CreateClient(RecordingHandler handler)
    {
        HttpClient http = new(handler) { BaseAddress = new Uri("http://keycloak:8080/") };
        return new KeycloakAdminClient(
            http,
            Options.Create(new KeycloakOptions
            {
                MetadataAddress = "http://keycloak:8080/auth/realms/vigia/.well-known/openid-configuration",
                ValidIssuer = "http://localhost:81/auth/realms/vigia",
                AdminUsername = "admin",
                AdminPassword = "admin",
            }),
            NullLogger<KeycloakAdminClient>.Instance);
    }

    private sealed class RecordingHandler : HttpMessageHandler
    {
        private readonly Queue<(HttpStatusCode Status, string Body)> _responses = new();

        public List<RecordedCall> Calls { get; } = [];

        public void Enqueue(HttpStatusCode status, string body) => _responses.Enqueue((status, body));

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            string body = request.Content is null
                ? string.Empty
                : await request.Content.ReadAsStringAsync(cancellationToken);
            Calls.Add(new RecordedCall(request.Method, request.RequestUri?.PathAndQuery ?? string.Empty, body));

            (HttpStatusCode status, string responseBody) = _responses.Dequeue();
            return new HttpResponseMessage(status)
            {
                Content = new StringContent(responseBody, Encoding.UTF8, "application/json"),
            };
        }
    }

    private sealed record RecordedCall(HttpMethod Method, string Path, string Body);
}
