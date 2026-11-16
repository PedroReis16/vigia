namespace Vigia.API.Contracts;

public sealed record UserPictureFile(byte[] Content, string ContentType);

public interface IUserPictureCleaner
{
    Task DeleteStoredPictureAsync(Guid userId, CancellationToken cancellationToken = default);
}
