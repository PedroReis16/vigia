namespace Vigia.API.Services.Users;

internal static class ProfilePictureFormat
{
    public const int MaxBytes = 2 * 1024 * 1024;

    public static string ObjectKey(Guid userId) => $"users/{userId:D}/avatar";

    public static bool TryDetect(ReadOnlySpan<byte> data, out string contentType)
    {
        if (data.Length >= 3 && data[0] == 0xFF && data[1] == 0xD8 && data[2] == 0xFF)
        {
            contentType = "image/jpeg";
            return true;
        }

        if (data.Length >= 8
            && data[0] == 0x89
            && data[1] == 0x50
            && data[2] == 0x4E
            && data[3] == 0x47
            && data[4] == 0x0D
            && data[5] == 0x0A
            && data[6] == 0x1A
            && data[7] == 0x0A)
        {
            contentType = "image/png";
            return true;
        }

        if (data.Length >= 12
            && data[0] == (byte)'R'
            && data[1] == (byte)'I'
            && data[2] == (byte)'F'
            && data[3] == (byte)'F'
            && data[8] == (byte)'W'
            && data[9] == (byte)'E'
            && data[10] == (byte)'B'
            && data[11] == (byte)'P')
        {
            contentType = "image/webp";
            return true;
        }

        contentType = string.Empty;
        return false;
    }
}
