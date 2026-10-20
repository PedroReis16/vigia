namespace Vigia.API.Contracts;

public interface IKeycloakAdminClient
{
    Task UpdateProfileAsync(
        Guid userId,
        string firstName,
        string lastName,
        string phone,
        CancellationToken cancellationToken = default);

    Task DeleteUserAsync(Guid userId, CancellationToken cancellationToken = default);
}
