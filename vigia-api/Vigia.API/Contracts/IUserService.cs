using Vigia.API.Models.DTOs.Auth;
using Vigia.API.Models.DTOs.Users;

namespace Vigia.API.Contracts;

public interface IUserService
{
    Task<List<UserDTO>> GetGroupUsersAsync(Guid id);
    Task RegisterNewUserAsync(NewUserDTO newUserDTO);

}