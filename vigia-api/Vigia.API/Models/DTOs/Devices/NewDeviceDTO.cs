namespace Vigia.API.Models.DTOs.Devices;

public record NewDeviceDTO(
    Guid Id,
    string Name,
    string MacAddress,
    string SignPublicKey
);