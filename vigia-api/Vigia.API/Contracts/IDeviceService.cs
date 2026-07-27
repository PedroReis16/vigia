using Vigia.API.Controllers;
using Vigia.API.Models.DTOs.Devices;

namespace Vigia.API.Contracts;

public interface IDeviceService
{
    Task RegisterDeviceAsync(NewDeviceDTO newDevice);
}