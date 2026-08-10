namespace Vigia.Cache.Services;

public interface IInMemoryCacheService
{
    object? Get(string key);
    void Add(string key, object value);
    void Remove(string key);
    void Clear();
}