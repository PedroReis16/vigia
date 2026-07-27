namespace Vigia.API.Models.DTOs.Devices;

public record NewDeviceDTO(
    Guid Id,
    string MacAddress,
    string PublicKey
);