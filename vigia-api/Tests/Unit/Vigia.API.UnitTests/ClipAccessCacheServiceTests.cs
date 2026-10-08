using Vigia.API.Contracts.CacheServices;
using Vigia.API.Services;
using Vigia.API.Services.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.UnitTests;

public class ClipAccessCacheServiceTests
{
    private readonly MemoryCache _cache = new();
    private readonly ClipAccessCacheService _service;
    private readonly ClipAccessTokenProvider _provider;

    public ClipAccessCacheServiceTests()
    {
        _service = new ClipAccessCacheService(_cache);
        _provider = new ClipAccessTokenProvider(_service);
    }

    [Fact]
    public void IssueToken_ReutilizaOTokenVigente()
    {
        Guid userId = Guid.NewGuid();
        Guid deviceId = Guid.NewGuid();

        string first = _service.IssueToken(userId, deviceId);
        _cache.Writes.Clear();
        string second = _service.IssueToken(userId, deviceId);

        Assert.Equal(first, second);
        Assert.Contains(_cache.Writes, write => write.Ttl == TimeSpan.FromHours(1));
    }

    [Fact]
    public void GetToken_RenovaOPrazo()
    {
        Guid userId = Guid.NewGuid();
        Guid deviceId = Guid.NewGuid();
        string token = _service.IssueToken(userId, deviceId);
        _cache.Writes.Clear();

        ClipAccessTokenEntry? entry = _service.GetToken(token);

        Assert.NotNull(entry);
        Assert.Equal(userId, entry.UserId);
        Assert.Equal(deviceId, entry.DeviceId);
        Assert.Equal(2, _cache.Writes.Count);
        Assert.All(_cache.Writes, write => Assert.Equal(TimeSpan.FromHours(1), write.Ttl));
    }

    [Fact]
    public void TryValidate_RecusaOutroDispositivo()
    {
        Guid userId = Guid.NewGuid();
        Guid deviceId = Guid.NewGuid();
        string token = _provider.IssueToken(userId, deviceId);

        Assert.True(_provider.TryValidate(token, deviceId, out Guid validated));
        Assert.Equal(userId, validated);
        Assert.False(_provider.TryValidate(token, Guid.NewGuid(), out _));
        Assert.False(_provider.TryValidate("missing", deviceId, out _));
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
