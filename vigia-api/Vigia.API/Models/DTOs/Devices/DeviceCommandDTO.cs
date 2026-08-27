
using Vigia.Models.Enums;

namespace Vigia.API.Models.DTOs.Devices;

public record DeviceCommandDTO(DeviceCommands Command, string? CommandValue = null);