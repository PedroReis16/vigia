using System.Net;
using System.Text.RegularExpressions;

namespace Vigia.Models.Helpers;

public static class Validators
{
    public static bool IsValidMacAddress(string macAddress)
    {
        Regex commomPattern = new(@"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", RegexOptions.Compiled);

        Regex ciscoPattern = new(@"^([0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})$", RegexOptions.Compiled);

        return !string.IsNullOrWhiteSpace(macAddress) && (commomPattern.IsMatch(macAddress) || ciscoPattern.IsMatch(macAddress));
    }

    /// <summary>Ed25519 raw public key encoded as 64 hex characters (32 bytes).</summary>
    public static bool IsValidEd25519PublicKeyHex(string? publicKeyHex)
    {
        if (string.IsNullOrWhiteSpace(publicKeyHex) || publicKeyHex.Length != 64)
            return false;

        return Regex.IsMatch(publicKeyHex, @"^[0-9A-Fa-f]{64}$", RegexOptions.Compiled);
    }

    public static bool ValidateIpAddress(this string ipAddress)
    {
        UriHostNameType hostName = Uri.CheckHostName(ipAddress);
        return hostName != UriHostNameType.Unknown;
    }

    public static bool IsPrivateIpAddress(string ipAddress)
    {
        if (string.IsNullOrWhiteSpace(ipAddress))
            return false;

        if (ipAddress is "localhost" or "127.0.0.1" or "::1")
            return true;

        // IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1)
        const string ipv4MappedPrefix = "::ffff:";
        if (ipAddress.StartsWith(ipv4MappedPrefix, StringComparison.OrdinalIgnoreCase))
            ipAddress = ipAddress[ipv4MappedPrefix.Length..];

        if (ipAddress.StartsWith("127."))
            return true;

        if (!IPAddress.TryParse(ipAddress, out IPAddress? parsed))
            return false;

        if (parsed.AddressFamily == System.Net.Sockets.AddressFamily.InterNetworkV6)
            return parsed.IsIPv6LinkLocal || parsed.IsIPv6UniqueLocal;

        byte[] bytes = parsed.GetAddressBytes();
        return bytes[0] == 10
            || (bytes[0] == 192 && bytes[1] == 168)
            || (bytes[0] == 172 && bytes[1] >= 16 && bytes[1] <= 31);
    }

}