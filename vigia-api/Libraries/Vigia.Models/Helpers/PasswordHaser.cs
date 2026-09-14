using System.Security.Cryptography;
using System.Text;
using Konscious.Security.Cryptography;

namespace Vigia.Models.Helpers;

public static class PasswordHasher
{
    public static byte[] Hash(string password, byte[] salt)
    {
        using var argon = new Argon2id(Encoding.UTF8.GetBytes(password))
        {
            Salt = salt,
            DegreeOfParallelism = 2,
            MemorySize = 1024 * 1024,
            Iterations = 4,
        };

        return argon.GetBytes(32);
    }

    public static byte[] GenerateSalt()
    {
        byte[] salt = new byte[16];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(salt);
        return salt;
    }
}