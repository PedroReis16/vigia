using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Auth;

namespace Vigia.API.Controllers;

[ApiController]
[Route("[controller]")]
public class AuthController(IUserService service) : ControllerBase
{
    private readonly IUserService _service = service;

    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] NewUserDTO newUserDTO)
    {
        await _service.RegisterNewUserAsync(newUserDTO);

        return CreatedAtAction(nameof(Login), new { email = newUserDTO.Email, password = newUserDTO.Password });
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginUserDTO loginUserDTO)
    {
        string? responseToken = await _service.LoginUserAsync(loginUserDTO);

        if (string.IsNullOrEmpty(responseToken))
            return Unauthorized();
            
        return Ok(responseToken);
    }

    [HttpPost("logout")]
    public async Task<IActionResult> Logout([FromHeader] string refreshToken)
    {
        return Ok();
    }

    [HttpPost("refresh")]
    public async Task<IActionResult> RefreshToken([FromBody] string refreshToken)
    {
        return Ok();
    }
}