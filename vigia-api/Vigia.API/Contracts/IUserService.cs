using Vigia.API.Models.DTOs.Auth;

namespace Vigia.API.Contracts;

public interface IUserService
{
    Task RegisterNewUserAsync(NewUserDTO newUserDTO);
    Task<string?> LoginUserAsync(LoginUserDTO loginUserDTO);

}