using System.Net;
using System.Text.Json;
using StackExchange.Redis;
using Vigia.Cache.Config;

namespace Vigia.Cache.Services;

public class RedisCacheService(RedisCacheConfig config, IConnectionMultiplexer connectionMultiplexer) : IRedisCacheService
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        ReferenceHandler = System.Text.Json.Serialization.ReferenceHandler.IgnoreCycles
    };

    protected readonly RedisCacheConfig Config = config;
    protected readonly IDatabase Database = connectionMultiplexer.GetDatabase();
    protected readonly IServer Server = GetServer(connectionMultiplexer);

    public virtual T? Get<T>(string key)
    {
        RedisValue value = Database.StringGet(NormalizeKey(key));
        if (value.IsNullOrEmpty)
            return default;

        if (typeof(T) == typeof(byte[]))
            return (T)(object)(byte[])value!;

        if (typeof(T) == typeof(string))
            return (T)(object)value.ToString();

        return JsonSerializer.Deserialize<T>(value.ToString(), SerializerOptions);
    }

    public virtual void Add<T>(string key, T value)
    {
        Add(key, value, TimeSpan.FromSeconds(Config.ExpirationInSeconds));
    }

    public virtual void Add<T>(string key, T value, TimeSpan expiration)
    {
        string redisKey = NormalizeKey(key);
        TimeSpan ttl = expiration > TimeSpan.Zero
            ? expiration
            : TimeSpan.FromSeconds(Config.ExpirationInSeconds);

        if (value is byte[] bytes)
        {
            _ = Database.StringSet(redisKey, bytes, ttl);
            return;
        }

        if (value is string text)
        {
            _ = Database.StringSet(redisKey, text, ttl);
            return;
        }

        string json = JsonSerializer.Serialize(value, SerializerOptions);
        _ = Database.StringSet(redisKey, json, ttl);
    }

    public virtual void Remove(string key)
    {
        _ = Database.KeyDelete(NormalizeKey(key));
    }

    public virtual void Clear()
    {
        foreach (RedisKey key in Server.Keys(pattern: $"{Config.InstanceName}*"))
            _ = Database.KeyDelete(key);
    }

    protected string NormalizeKey(string key) =>
        $"{Config.InstanceName}{key.ToUpperInvariant()}";

    private static IServer GetServer(IConnectionMultiplexer connectionMultiplexer)
    {
        EndPoint endPoint = connectionMultiplexer.GetEndPoints().First();
        return connectionMultiplexer.GetServer(endPoint);
    }
}
