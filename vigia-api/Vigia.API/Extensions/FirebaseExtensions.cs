using System.Text;
using FirebaseAdmin;
using Google.Apis.Auth.OAuth2;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts;
using Vigia.API.Services;

namespace Vigia.API.Extensions;

public static class FirebaseExtensions
{
    public static IServiceCollection AddFirebasePushNotifications(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.Configure<FirebaseOptions>(configuration.GetSection(FirebaseOptions.SectionName));
        services.AddSingleton<IPushNotificationService, FirebasePushNotificationService>();

        FirebaseOptions options = configuration.GetSection(FirebaseOptions.SectionName).Get<FirebaseOptions>()
            ?? new FirebaseOptions();

        if (FirebaseApp.DefaultInstance is not null)
            return services;

        GoogleCredential? credential = TryLoadCredential(options);
        if (credential is null)
            return services;

        FirebaseApp.Create(new AppOptions
        {
            Credential = credential,
        });

        return services;
    }

    private static GoogleCredential? TryLoadCredential(FirebaseOptions options)
    {
        if (!string.IsNullOrWhiteSpace(options.CredentialJson))
        {
            string? json = TryDecodeCredentialJson(options.CredentialJson);
            if (json is null)
            {
                Console.WriteLine(
                    "warn: Firebase CredentialJson is not valid JSON or Base64. Push notifications disabled.");
                return null;
            }

            return GoogleCredential.FromJson(json);
        }

        if (string.IsNullOrWhiteSpace(options.CredentialPath))
            return null;

        string path = ExpandHomeDirectory(options.CredentialPath);
        if (File.Exists(path))
            return GoogleCredential.FromFile(path);

        Console.WriteLine(
            $"warn: Firebase credential file not found at '{path}' " +
            $"(configured CredentialPath='{options.CredentialPath}'). Push notifications disabled.");
        return null;
    }

    private static string? TryDecodeCredentialJson(string value)
    {
        string trimmed = value.Trim();
        if (trimmed.Length == 0)
            return null;

        if (trimmed.StartsWith('{'))
            return trimmed;

        string base64 = trimmed
            .Replace("-", "+", StringComparison.Ordinal)
            .Replace("_", "/", StringComparison.Ordinal)
            .Replace("\r", string.Empty, StringComparison.Ordinal)
            .Replace("\n", string.Empty, StringComparison.Ordinal)
            .Replace(" ", string.Empty, StringComparison.Ordinal);

        int pad = base64.Length % 4;
        if (pad != 0)
            base64 = base64.PadRight(base64.Length + (4 - pad), '=');

        try
        {
            string json = Encoding.UTF8.GetString(Convert.FromBase64String(base64));
            return json.TrimStart().StartsWith('{') ? json : null;
        }
        catch (FormatException)
        {
            return null;
        }
    }

    private static string ExpandHomeDirectory(string path)
    {
        if (path is "~")
            return Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);

        if (path.StartsWith("~/", StringComparison.Ordinal) || path.StartsWith("~\\", StringComparison.Ordinal))
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                path[2..]);
        }

        return path;
    }
}
