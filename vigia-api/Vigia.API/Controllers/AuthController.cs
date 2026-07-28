using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
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
    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] NewUserDTO newUserDTO)
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        IUserService userService = scope.ServiceProvider.GetRequiredService<IUserService>();

        await userService.RegisterNewUserAsync(newUserDTO);

        return CreatedAtAction(nameof(Login), new { email = newUserDTO.Email, password = newUserDTO.Password });
    }

    /// <summary>
    /// Realiza a autenticação do usuário e retorna um token de acesso e um token de atualização
    /// </summary>
    /// <param name="loginUserDTO"></param>
    /// <returns></returns>
    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginUserDTO loginUserDTO)
    {
        string requestIp = HttpContext.Connection.RemoteIpAddress?.ToString() ?? "Unknown";

        using IServiceScope scope = _scopeFactory.CreateScope();
        IAuthService authService = scope.ServiceProvider.GetRequiredService<IAuthService>();

        AuthResponseDTO? responseToken = await authService.LoginUserAsync(loginUserDTO, requestIp);

        if (responseToken == null)
            return Unauthorized();

        return Ok(responseToken);
    }

    /// <summary>
    /// Renova o token de acesso
    /// </summary>
    /// <param name="refreshToken"></param>
    /// <returns></returns>
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

        Guid tokenId = (Guid)HttpContext.Items["tokenId"]!;
        DateTime expiresAt = (DateTime)HttpContext.Items["expiresAt"]!;

        IAuthService authService = scope.ServiceProvider.GetRequiredService<IAuthService>();

        await authService.LogoutUserAsync(tokenId, expiresAt, refreshToken.RefreshToken);

        return NoContent();
    }


}