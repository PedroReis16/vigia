using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Auth;

namespace Vigia.API.Controllers;

[ApiController]
[Route("[controller]")]
public class AuthController(IServiceScopeFactory scopeFactory) : ControllerBase
{
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    /// <summary>
    /// Registra um novo usuário no sistema
    /// </summary>
    /// <param name="newUserDTO"></param>
    /// <returns></returns>
    [AllowAnonymous]
    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] NewUserDTO newUserDTO)
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        IUserService userService = scope.ServiceProvider.GetRequiredService<IUserService>();
        
        await userService.RegisterNewUserAsync(newUserDTO);
        AuthResponseDTO? responseToken = await LogingUser(new LoginUserDTO(newUserDTO.Email, newUserDTO.Password));
        if (responseToken == null)
            return Unauthorized();

        return CreatedAtAction(nameof(Login), responseToken);
    }

    /// <summary>
    /// Realiza a autenticação do usuário e retorna um token de acesso e um token de atualização
    /// </summary>
    /// <param name="loginUserDTO"></param>
    /// <returns></returns>
    [AllowAnonymous]
    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginUserDTO loginUserDTO)
    {
        AuthResponseDTO? responseToken = await LogingUser(loginUserDTO);
        if (responseToken == null)
            return Unauthorized();

        return Ok(responseToken);
    }

    private async Task<AuthResponseDTO?> LogingUser(LoginUserDTO loginUser)
    {
        string requestIp = HttpContext.Connection.RemoteIpAddress?.ToString() ?? "Unknown";

        using IServiceScope scope = _scopeFactory.CreateScope();
        IAuthService authService = scope.ServiceProvider.GetRequiredService<IAuthService>();

        AuthResponseDTO? responseToken = await authService.LoginUserAsync(loginUser, requestIp);
        return responseToken;
    }

    /// <summary>
    /// Renova o token de acesso
    /// </summary>
    /// <param name="refreshToken"></param>
    /// <returns></returns>
    [AllowAnonymous]
    [HttpPost("refresh")]
    public async Task<IActionResult> RefreshToken([FromBody] RefreshTokenDTO refreshToken)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();

            string requestIp = HttpContext.Connection.RemoteIpAddress?.ToString() ?? "Unknown";

            IAuthService authService = scope.ServiceProvider.GetRequiredService<IAuthService>();

            AuthResponseDTO? responseToken = await authService.RefreshTokenAsync(refreshToken.RefreshToken, requestIp);

            if (responseToken == null)
                return Unauthorized();

            return Ok(responseToken);
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized();
        }
        catch (Exception)
        {
            throw;
        }
    }

    /// <summary>
    /// Revoga a sessão do usuário e invalida o token de atualização
    /// </summary>
    /// <param name="refreshToken"></param>
    /// <returns></returns>
    [HttpPost("logout")]
    public async Task<IActionResult> Logout([FromBody] RefreshTokenDTO refreshToken)
    {
        using IServiceScope scope = _scopeFactory.CreateScope();

        Guid tokenId = User.GetTokenId();
        DateTime expiresAt = User.GetExpiresAt();

        IAuthService authService = scope.ServiceProvider.GetRequiredService<IAuthService>();

        await authService.LogoutUserAsync(tokenId, expiresAt, refreshToken.RefreshToken);

        return NoContent();
    }


}