namespace Vigia.API.Services.Clips;

internal static class ClipObjectKeys
{
    public static string For(Guid deviceId, Guid clipId) => $"clips/{deviceId:D}/{clipId:D}.mp4";

    public static string Poster(Guid deviceId, Guid clipId) => $"clips/{deviceId:D}/{clipId:D}.jpg";
}
