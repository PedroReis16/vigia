using Vigia.API.Models.DTOs.Users;

namespace Vigia.API.Contracts;

public interface IKeycloakUserSyncService
{
    Task ApplyAsync(KeycloakUserSyncMessage message);
}
