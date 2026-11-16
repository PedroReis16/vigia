using Vigia.API.Contracts.CacheServices;
using Vigia.API.Services;
using Vigia.API.Services.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.UnitTests;

public class PictureAccessCacheServiceTests
{
    private readonly MemoryCache _cache = new();
    private readonly PictureAccessCacheService _service;
    private readonly PictureAccessTokenProvider _provider;

    public PictureAccessCacheServiceTests()
    {
        _service = new PictureAccessCacheService(_cache);
        _provider = new PictureAccessTokenProvider(_service);
    }

    [Fact]
    public void IssueToken_ReutilizaOTokenVigente()
    {
        Guid viewerId = Guid.NewGuid();
        Guid subjectId = Guid.NewGuid();

        string first = _service.IssueToken(viewerId, subjectId);
        string second = _service.IssueToken(viewerId, subjectId);

        Assert.Equal(first, second);
    }

    [Fact]
    public void TryValidate_RecusaOutroUsuario()
    {
        Guid viewerId = Guid.NewGuid();
        Guid subjectId = Guid.NewGuid();
        string token = _provider.IssueToken(viewerId, subjectId);

        Assert.True(_provider.TryValidate(token, subjectId, out Guid viewer));
        Assert.Equal(viewerId, viewer);
        Assert.False(_provider.TryValidate(token, Guid.NewGuid(), out _));
        Assert.False(_provider.TryValidate("missing", subjectId, out _));
    }

    [Fact]
    public void GetToken_RenovaOPrazo()
    {
        string token = _service.IssueToken(Guid.NewGuid(), Guid.NewGuid());
        _cache.Writes.Clear();

        PictureAccessTokenEntry? entry = _service.GetToken(token);

        Assert.NotNull(entry);
        Assert.Equal(2, _cache.Writes.Count);
        Assert.All(_cache.Writes, write => Assert.Equal(TimeSpan.FromHours(1), write.Ttl));
    }

    private sealed class MemoryCache : IRedisCacheService
    {
        private readonly Dictionary<string, object> _items = [];

        public List<(string Key, TimeSpan? Ttl)> Writes { get; } = [];

        public T? Get<T>(string key) => _items.TryGetValue(key, out object? value) && value is T typed ? typed : default;

        public bool Exists(string key) => _items.ContainsKey(key);

        public void Add<T>(string key, T value)
        {
            _items[key] = value!;
            Writes.Add((key, null));
        }

        public void Add<T>(string key, T value, TimeSpan expiration)
        {
            _items[key] = value!;
            Writes.Add((key, expiration));
        }

        public void Remove(string key) => _items.Remove(key);

        public void Clear() => _items.Clear();
    }
}
