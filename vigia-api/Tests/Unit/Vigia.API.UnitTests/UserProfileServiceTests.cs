using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Users;
using Vigia.API.Services;
using Vigia.API.Services.CacheServices;
using Vigia.API.Services.Users;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;
using Vigia.Models.Seed;

namespace Vigia.API.UnitTests;

public class UserProfileServiceTests
{
    private readonly VigiaDbContext _context;
    private readonly MemoryCloud _cloud = new();
    private readonly FakeKeycloakAdmin _keycloak = new();
    private readonly UserProfileService _service;
    private readonly Guid _userId = Guid.NewGuid();

    public UserProfileServiceTests()
    {
        _context = CreateContext();
        _context.Users.Add(new User
        {
            Id = _userId,
            FirstName = "Ana",
            LastName = "Lima",
            Email = "ana@vigia.test",
            Phone = "11999990000",
        });
        _context.SaveChanges();

        PictureAccessCacheService cache = new(new MemoryCache());
        _service = new UserProfileService(
            new UserDao(_context),
            new UserPushTokenDao(_context),
            _keycloak,
            _cloud,
            Options.Create(new CloudOptions { PicturesBucketName = "vigia-pictures" }),
            new PictureAccessTokenProvider(cache),
            NullLogger<UserProfileService>.Instance);
    }

    [Fact]
    public async Task GetAsync_UsesEmailWhenTheNameIsEmpty()
    {
        Guid userId = Guid.NewGuid();
        _context.Users.Add(new User
        {
            Id = userId,
            Email = "sem-nome@vigia.test",
            Phone = "1",
        });
        await _context.SaveChangesAsync();

        var profile = await _service.GetAsync(userId);

        Assert.Equal("sem-nome@vigia.test", profile.Name);
        Assert.Null(profile.PictureUrl);
        Assert.True(profile.CanDeleteAccount);
    }

    [Fact]
    public async Task SavePictureAsync_StoresJpegAndReturnsAPictureUrl()
    {
        byte[] jpeg = [0xFF, 0xD8, 0xFF, 0x00];

        var profile = await _service.SavePictureAsync(_userId, new MemoryStream(jpeg), jpeg.Length);

        Assert.Equal("Ana Lima", profile.Name);
        Assert.Equal($"users/{_userId:D}/avatar", _cloud.Objects.Keys.Single());
        Assert.Equal(jpeg, _cloud.Objects[$"users/{_userId:D}/avatar"]);
        Assert.Contains($"users/{_userId:D}/picture?accessToken=", profile.PictureUrl);
        Assert.Contains("&v=", profile.PictureUrl);

        UserPictureFile? file = await _service.OpenPictureAsync(_userId);
        Assert.NotNull(file);
        Assert.Equal("image/jpeg", file.ContentType);
        Assert.Equal(jpeg, file.Content);
    }

    [Fact]
    public async Task SavePictureAsync_RejectsTextAndOversizedFiles()
    {
        byte[] text = "not-an-image"u8.ToArray();
        EntityValidationException invalid = await Assert.ThrowsAsync<EntityValidationException>(
            () => _service.SavePictureAsync(_userId, new MemoryStream(text), text.Length));
        Assert.Equal(ErrorCodes.INVALID_PROFILE_PICTURE, invalid.ErrorCode);

        EntityValidationException huge = await Assert.ThrowsAsync<EntityValidationException>(
            () => _service.SavePictureAsync(_userId, new MemoryStream([0xFF]), ProfilePictureFormat.MaxBytes + 1));
        Assert.Equal(ErrorCodes.PROFILE_PICTURE_TOO_LARGE, huge.ErrorCode);
        Assert.Empty(_cloud.Objects);
    }

    [Fact]
    public async Task RemovePictureAsync_DeletesTheObject()
    {
        byte[] png = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00];
        await _service.SavePictureAsync(_userId, new MemoryStream(png), png.Length);

        var profile = await _service.RemovePictureAsync(_userId);

        Assert.Null(profile.PictureUrl);
        Assert.Empty(_cloud.Objects);
        User user = await _context.Users.SingleAsync(u => u.Id == _userId);
        Assert.Null(user.PictureKey);
    }

    [Fact]
    public async Task DeleteStoredPictureAsync_ClearsTheKeyOnSoftDeletePath()
    {
        byte[] webp = "RIFF0000WEBP"u8.ToArray();
        await _service.SavePictureAsync(_userId, new MemoryStream(webp), webp.Length);

        await _service.DeleteStoredPictureAsync(_userId);

        Assert.Empty(_cloud.Objects);
        Assert.Null(await _service.OpenPictureAsync(_userId));
    }

    [Fact]
    public async Task UpdateAsync_WritesKeycloakAndTheLocalProfile()
    {
        var profile = await _service.UpdateAsync(_userId, new UpdateUserProfileDTO
        {
            FirstName = " Ana ",
            LastName = "Souza",
            Phone = "(11) 98888-0000",
        });

        Assert.Equal("Ana Souza", profile.Name);
        Assert.Equal(("Ana", "Souza", "(11) 98888-0000"), _keycloak.Updated);
        User user = await _context.Users.SingleAsync(u => u.Id == _userId);
        Assert.Equal("Ana", user.FirstName);
        Assert.Equal("Souza", user.LastName);
        Assert.Equal("(11) 98888-0000", user.Phone);
    }

    [Fact]
    public async Task UpdateAsync_RejectsAnInvalidPhoneWithoutCallingKeycloak()
    {
        EntityValidationException error = await Assert.ThrowsAsync<EntityValidationException>(() =>
            _service.UpdateAsync(_userId, new UpdateUserProfileDTO
            {
                FirstName = "Ana",
                LastName = "Lima",
                Phone = "abc",
            }));

        Assert.Equal(ErrorCodes.INVALID_PROFILE_PHONE, error.ErrorCode);
        Assert.Null(_keycloak.Updated);
    }

    [Fact]
    public async Task UpdateAsync_KeepsTheLocalProfileWhenKeycloakRejectsTheChange()
    {
        _keycloak.Failure = new EntityValidationException("profile", "falhou", ErrorCodes.PROFILE_UPDATE_FAILED);

        await Assert.ThrowsAsync<EntityValidationException>(() =>
            _service.UpdateAsync(_userId, new UpdateUserProfileDTO
            {
                FirstName = "Bia",
                LastName = "Costa",
                Phone = "11988887777",
            }));

        User user = await _context.Users.SingleAsync(u => u.Id == _userId);
        Assert.Equal("Ana", user.FirstName);
        Assert.Equal("Lima", user.LastName);
    }

    [Fact]
    public async Task DeleteAccountAsync_RemovesKeycloakUserPictureAndPushTokens()
    {
        byte[] jpeg = [0xFF, 0xD8, 0xFF, 0x00];
        await _service.SavePictureAsync(_userId, new MemoryStream(jpeg), jpeg.Length);
        _context.UserPushTokens.Add(new UserPushToken
        {
            Id = Guid.NewGuid(),
            UserId = _userId,
            Token = "fcm-1",
            Platform = "web",
        });
        await _context.SaveChangesAsync();

        await _service.DeleteAccountAsync(_userId);

        Assert.True(_keycloak.Deleted);
        Assert.Empty(_cloud.Objects);
        User user = await _context.Users.SingleAsync(u => u.Id == _userId);
        Assert.NotNull(user.DeletedAt);
        Assert.All(_context.UserPushTokens.Where(t => t.UserId == _userId), token => Assert.NotNull(token.DeletedAt));
    }

    [Fact]
    public async Task GetAsync_HidesAccountDeletionForTheSuperAdmin()
    {
        _context.Users.Add(new User
        {
            Id = TestDeviceSeed.OwnerId,
            FirstName = "Super",
            LastName = "Admin",
            Email = TestDeviceSeed.OwnerEmail,
            Phone = TestDeviceSeed.OwnerPhone,
        });
        await _context.SaveChangesAsync();

        var profile = await _service.GetAsync(TestDeviceSeed.OwnerId);

        Assert.False(profile.CanDeleteAccount);
    }

    [Fact]
    public async Task DeleteAccountAsync_RejectsTheSuperAdmin()
    {
        _context.Users.Add(new User
        {
            Id = Guid.NewGuid(),
            FirstName = "Outro",
            LastName = "Admin",
            Email = TestDeviceSeed.OwnerEmail,
            Phone = "11988887777",
        });
        await _context.SaveChangesAsync();
        Guid userId = _context.Users.Single(u => u.Email == TestDeviceSeed.OwnerEmail).Id;

        EntityValidationException error = await Assert.ThrowsAsync<EntityValidationException>(() =>
            _service.DeleteAccountAsync(userId));

        Assert.Equal(ErrorCodes.ACCOUNT_DELETE_FORBIDDEN, error.ErrorCode);
        Assert.False(_keycloak.Deleted);
        User user = await _context.Users.SingleAsync(u => u.Id == userId);
        Assert.Null(user.DeletedAt);
    }

    private static VigiaDbContext CreateContext()
    {
        DbContextOptions<VigiaDbContext> options = new DbContextOptionsBuilder<VigiaDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        VigiaDbContext context = new(options);
        context.Database.EnsureCreated();
        return context;
    }

    private sealed class MemoryCloud : ICloudService
    {
        public Dictionary<string, byte[]> Objects { get; } = [];

        public Task EnsureBucketAsync(string bucketName, CancellationToken cancellationToken = default) => Task.CompletedTask;

        public async Task UploadFileAsync(string bucketName, string key, Stream content, string? contentType = null, CancellationToken cancellationToken = default)
        {
            using MemoryStream buffer = new();
            await content.CopyToAsync(buffer, cancellationToken);
            Objects[key] = buffer.ToArray();
        }

        public Task<Stream> DownloadFileAsync(string bucketName, string key, CancellationToken cancellationToken = default)
        {
            if (!Objects.TryGetValue(key, out byte[]? bytes))
                throw new FileNotFoundException(key);

            return Task.FromResult<Stream>(new MemoryStream(bytes));
        }

        public Task<long?> TryGetObjectLengthAsync(string bucketName, string key, CancellationToken cancellationToken = default) =>
            Task.FromResult(Objects.TryGetValue(key, out byte[]? bytes) ? bytes.Length : (long?)null);

        public Task<CloudObjectRead> OpenRangeAsync(string bucketName, string key, long? start, long? end, CancellationToken cancellationToken = default) =>
            throw new NotSupportedException();

        public Task<IReadOnlyList<string>> ListKeysAsync(string bucketName, CancellationToken cancellationToken = default) =>
            Task.FromResult<IReadOnlyList<string>>(Objects.Keys.ToList());

        public Task DeleteFileAsync(string bucketName, string key, CancellationToken cancellationToken = default)
        {
            Objects.Remove(key);
            return Task.CompletedTask;
        }
    }

    private sealed class MemoryCache : Vigia.Cache.Services.IRedisCacheService
    {
        private readonly Dictionary<string, object> _items = [];

        public T? Get<T>(string key) => _items.TryGetValue(key, out object? value) && value is T typed ? typed : default;

        public bool Exists(string key) => _items.ContainsKey(key);

        public void Add<T>(string key, T value) => _items[key] = value!;

        public void Add<T>(string key, T value, TimeSpan expiration) => _items[key] = value!;

        public void Remove(string key) => _items.Remove(key);

        public void Clear() => _items.Clear();
    }

    private sealed class FakeKeycloakAdmin : IKeycloakAdminClient
    {
        public Exception? Failure { get; set; }
        public (string First, string Last, string Phone)? Updated { get; private set; }
        public bool Deleted { get; private set; }

        public Task UpdateProfileAsync(
            Guid userId,
            string firstName,
            string lastName,
            string phone,
            CancellationToken cancellationToken = default)
        {
            if (Failure is not null)
                throw Failure;

            Updated = (firstName, lastName, phone);
            return Task.CompletedTask;
        }

        public Task DeleteUserAsync(Guid userId, CancellationToken cancellationToken = default)
        {
            if (Failure is not null)
                throw Failure;

            Deleted = true;
            return Task.CompletedTask;
        }
    }
}
