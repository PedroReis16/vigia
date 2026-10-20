namespace Vigia.Models.Enums;

public enum DeviceCommands
{
    START_STREAMING = 1,
    STOP_STREAMING = 2,
    DEVICE_ON = 3,
    DEVICE_OFF = 4,
    DEVICE_UPDATE = 5,
    CLIPS_ON = 6,
    CLIPS_OFF = 7,
    BLUR_ON = 8,
    BLUR_OFF = 9
}

public static class DeviceCommandExtensions
{
    public static string GetCommandName(this DeviceCommands command)
    {
        return command switch
        {
            DeviceCommands.START_STREAMING => "stream_on",
            DeviceCommands.STOP_STREAMING => "stream_off",
            DeviceCommands.DEVICE_ON => "device_on",
            DeviceCommands.DEVICE_OFF => "device_off",
            DeviceCommands.DEVICE_UPDATE => "device_update",
            DeviceCommands.CLIPS_ON => "clips_on",
            DeviceCommands.CLIPS_OFF => "clips_off",
            DeviceCommands.BLUR_ON => "blur_on",
            DeviceCommands.BLUR_OFF => "blur_off",
            _ => throw new ArgumentException("Invalid device command")
        };
    }
}