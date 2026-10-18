using Vigia.API.Models.DTOs.Users;

namespace Vigia.API.Contracts;

public interface IUserProfileService
{
    Task<UserProfileDTO> GetAsync(Guid userId, CancellationToken cancellationToken = default);

    Task<UserProfileDTO> UpdateAsync(Guid userId, UpdateUserProfileDTO profile, CancellationToken cancellationToken = default);

    Task DeleteAccountAsync(Guid userId, CancellationToken cancellationToken = default);

    Task<UserProfileDTO> SavePictureAsync(Guid userId, Stream content, long length, CancellationToken cancellationToken = default);

    Task<UserProfileDTO> RemovePictureAsync(Guid userId, CancellationToken cancellationToken = default);

    Task<UserPictureFile?> OpenPictureAsync(Guid subjectUserId, CancellationToken cancellationToken = default);
}
