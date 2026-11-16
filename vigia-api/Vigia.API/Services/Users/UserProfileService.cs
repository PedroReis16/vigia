using Microsoft.Extensions.Options;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Users;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Database.Contracts;
using Vigia.Models.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services.Users;

internal class UserProfileService(
    IUserDao userDao,
    IUserPushTokenDao pushTokenDao,
    IKeycloakAdminClient keycloakAdmin,
    ICloudService cloud,
    IOptions<CloudOptions> cloudOptions,
    IPictureAccessTokenProvider pictureAccess,
    ILogger<UserProfileService> logger) : IUserProfileService, IUserPictureCleaner
{
    private readonly IUserDao _userDao = userDao;
    private readonly IUserPushTokenDao _pushTokenDao = pushTokenDao;
    private readonly IKeycloakAdminClient _keycloakAdmin = keycloakAdmin;
    private readonly ICloudService _cloud = cloud;
    private readonly CloudOptions _cloudOptions = cloudOptions.Value;
    private readonly IPictureAccessTokenProvider _pictureAccess = pictureAccess;
    private readonly ILogger<UserProfileService> _logger = logger;

    public async Task<UserProfileDTO> GetAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        User user = await RequireUserAsync(userId);
        return ToDto(user);
    }

    public async Task<UserProfileDTO> UpdateAsync(
        Guid userId,
        UpdateUserProfileDTO profile,
        CancellationToken cancellationToken = default)
    {
        User user = await RequireUserAsync(userId);
        string firstName = ProfileFieldRules.RequireName(profile.FirstName, nameof(profile.FirstName));
        string lastName = ProfileFieldRules.RequireName(profile.LastName, nameof(profile.LastName));
        string phone = ProfileFieldRules.RequirePhone(profile.Phone);

        await _keycloakAdmin.UpdateProfileAsync(userId, firstName, lastName, phone, cancellationToken);
        await _userDao.UpdateProfileAsync(userId, firstName, lastName, phone);

        user.FirstName = firstName;
        user.LastName = lastName;
        user.Phone = phone;
        user.UpdatedAt = DateTime.UtcNow;
        return ToDto(user);
    }

    public async Task DeleteAccountAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        User user = await RequireUserAsync(userId);
        AccountDeletionRules.EnsureCanDelete(user);
        await _keycloakAdmin.DeleteUserAsync(userId, cancellationToken);
        await DeleteStoredPictureAsync(userId, cancellationToken);
        await _userDao.SoftDeleteAsync(userId);
        await _pushTokenDao.DeleteByUserIdAsync(userId);
    }

    public async Task<UserProfileDTO> SavePictureAsync(
        Guid userId,
        Stream content,
        long length,
        CancellationToken cancellationToken = default)
    {
        User user = await RequireUserAsync(userId);
        byte[] bytes = await ReadLimitedAsync(content, length, cancellationToken);
        if (!ProfilePictureFormat.TryDetect(bytes, out string contentType))
            throw new EntityValidationException(nameof(content), "A foto precisa ser JPEG, PNG ou WebP", ErrorCodes.INVALID_PROFILE_PICTURE);

        string key = ProfilePictureFormat.ObjectKey(userId);
        string bucket = RequireBucket();
        await using MemoryStream upload = new(bytes, writable: false);
        await _cloud.UploadFileAsync(bucket, key, upload, contentType, cancellationToken);
        await _userDao.SetPictureKeyAsync(userId, key);

        user.PictureKey = key;
        user.UpdatedAt = DateTime.UtcNow;
        return ToDto(user);
    }

    public async Task<UserProfileDTO> RemovePictureAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        User user = await RequireUserAsync(userId);
        await DeleteObjectAsync(user.PictureKey, cancellationToken);
        await _userDao.SetPictureKeyAsync(userId, null);

        user.PictureKey = null;
        user.UpdatedAt = DateTime.UtcNow;
        return ToDto(user);
    }

    public async Task DeleteStoredPictureAsync(Guid userId, CancellationToken cancellationToken = default)
    {
        User? user = await _userDao.FindAsync(userId);
        if (user is null || string.IsNullOrWhiteSpace(user.PictureKey))
            return;

        await DeleteObjectAsync(user.PictureKey, cancellationToken);
        await _userDao.SetPictureKeyAsync(userId, null);
    }

    public async Task<UserPictureFile?> OpenPictureAsync(Guid subjectUserId, CancellationToken cancellationToken = default)
    {
        User? user = await _userDao.FindAsync(subjectUserId);
        if (user is null || string.IsNullOrWhiteSpace(user.PictureKey))
            return null;

        try
        {
            await using Stream stream = await _cloud.DownloadFileAsync(RequireBucket(), user.PictureKey, cancellationToken);
            using MemoryStream buffer = new();
            await stream.CopyToAsync(buffer, cancellationToken);
            byte[] bytes = buffer.ToArray();
            if (!ProfilePictureFormat.TryDetect(bytes, out string contentType))
                return null;

            return new UserPictureFile(bytes, contentType);
        }
        catch (FileNotFoundException)
        {
            return null;
        }
    }

    private UserProfileDTO ToDto(User user)
    {
        string? pictureUrl = null;
        if (!string.IsNullOrWhiteSpace(user.PictureKey))
            pictureUrl = UserPictureUrls.For(user, _pictureAccess.IssueToken(user.Id, user.Id));

        return new UserProfileDTO
        {
            Id = user.Id,
            Name = UserDisplayName.Format(user.FirstName, user.LastName, user.Email),
            FirstName = user.FirstName,
            LastName = user.LastName,
            Email = user.Email,
            Phone = user.Phone,
            PictureUrl = pictureUrl,
            CanDeleteAccount = AccountDeletionRules.CanDelete(user),
        };
    }

    private async Task<User> RequireUserAsync(Guid userId)
    {
        User? user = await _userDao.FindAsync(userId);
        if (user is null)
            throw new EntityValidationException(nameof(User), "Usuário não encontrado", ErrorCodes.USER_NOT_FOUND);

        return user;
    }

    private string RequireBucket()
    {
        if (string.IsNullOrWhiteSpace(_cloudOptions.PicturesBucketName))
            throw new InvalidOperationException("Cloud:PicturesBucketName não está configurado");

        return _cloudOptions.PicturesBucketName;
    }

    private async Task DeleteObjectAsync(string? pictureKey, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(pictureKey))
            return;

        try
        {
            await _cloud.DeleteFileAsync(RequireBucket(), pictureKey, cancellationToken);
        }
        catch (Exception ex) when (ex is not InvalidOperationException)
        {
            _logger.LogWarning(ex, "Não foi possível apagar a foto de perfil {PictureKey}", pictureKey);
        }
    }

    private static async Task<byte[]> ReadLimitedAsync(Stream content, long length, CancellationToken cancellationToken)
    {
        if (length > ProfilePictureFormat.MaxBytes)
            throw new EntityValidationException(nameof(content), "A foto passa de 2 MB", ErrorCodes.PROFILE_PICTURE_TOO_LARGE);

        using MemoryStream buffer = new();
        byte[] chunk = new byte[81920];
        int read;
        while ((read = await content.ReadAsync(chunk, cancellationToken)) > 0)
        {
            if (buffer.Length + read > ProfilePictureFormat.MaxBytes)
                throw new EntityValidationException(nameof(content), "A foto passa de 2 MB", ErrorCodes.PROFILE_PICTURE_TOO_LARGE);

            buffer.Write(chunk, 0, read);
        }

        if (buffer.Length == 0)
            throw new EntityValidationException(nameof(content), "A foto é obrigatória", ErrorCodes.INVALID_PROFILE_PICTURE);

        return buffer.ToArray();
    }
}
