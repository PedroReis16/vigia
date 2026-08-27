namespace Vigia.Cache.Services;

public interface IRedisCacheService
{
    T? Get<T>(string key);
    bool Exists(string key);
    void Add<T>(string key, T value);
    void Add<T>(string key, T value, TimeSpan expiration);
    void Remove(string key);
    void Clear();
}
