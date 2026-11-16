using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Vigia.API.Contracts;
using Vigia.API.Helpers;
using Vigia.API.Models.DTOs.Users;
using Vigia.API.Services.Users;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;
using Vigia.Models.Middlewares;

namespace Vigia.API.Controllers;

[ApiController]
[Route("users")]
[Authorize]
public class UserController(
    IUserPushTokenService pushTokenService,
    IUserLogoutService logoutService,
    IUserProfileService profileService) : ControllerBase
{
    private readonly IUserPushTokenService _pushTokenService = pushTokenService;
    private readonly IUserLogoutService _logoutService = logoutService;
    private readonly IUserProfileService _profileService = profileService;

    /// <summary>
    /// Registra ou atualiza o token FCM do aparelho do usuário autenticado.
    /// </summary>
    [HttpPut("push-token")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public async Task<IActionResult> UpsertPushToken([FromBody] UpsertPushTokenDTO dto)
    {
        Guid userId = User.GetUserId();
        await _pushTokenService.UpsertPushTokenAsync(userId, dto.Token, dto.Platform);
        return NoContent();
    }

    /// <summary>
    /// Remove o token FCM do aparelho (ex.: logout parcial / limpeza local).
    /// </summary>
    [HttpDelete("push-token")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public async Task<IActionResult> DeletePushToken([FromBody] DeletePushTokenDTO dto)
    {
        Guid userId = User.GetUserId();
        await _pushTokenService.DeletePushTokenAsync(userId, dto.Token);
        return NoContent();
    }

    /// <summary>
    /// Encerra a sessão no Keycloak e, se aceito, remove o push token deste aparelho.
    /// </summary>
    [HttpPost("logout")]
    [ProducesResponseType(typeof(LogoutResponseDTO), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<LogoutResponseDTO>> Logout(
        [FromBody] LogoutRequestDTO dto,
        CancellationToken cancellationToken)
    {
        LogoutResponseDTO result = await _logoutService.LogoutAsync(
            User.GetUserId(),
            User.GetAuthorizedParty(),
            dto,
            cancellationToken);

        return Ok(result);
    }

    /// <summary>
    /// Nome, e-mail, telefone e URL da foto do usuário autenticado.
    /// </summary>
    [HttpGet("me")]
    [ProducesResponseType(typeof(UserProfileDTO), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<UserProfileDTO>> GetProfile(CancellationToken cancellationToken)
    {
        UserProfileDTO profile = await _profileService.GetAsync(User.GetUserId(), cancellationToken);
        return Ok(profile);
    }

    /// <summary>
    /// Atualiza nome e telefone no Keycloak e na base local.
    /// </summary>
    [HttpPut("me")]
    [ProducesResponseType(typeof(UserProfileDTO), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<UserProfileDTO>> UpdateProfile(
        [FromBody] UpdateUserProfileDTO dto,
        CancellationToken cancellationToken)
    {
        UserProfileDTO profile = await _profileService.UpdateAsync(User.GetUserId(), dto, cancellationToken);
        return Ok(profile);
    }

    /// <summary>
    /// Apaga a conta no Keycloak e remove foto, sessão local e tokens de push.
    /// </summary>
    [HttpDelete("me")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> DeleteAccount(CancellationToken cancellationToken)
    {
        await _profileService.DeleteAccountAsync(User.GetUserId(), cancellationToken);
        return NoContent();
    }

    /// <summary>
    /// Substitui a foto de perfil. JPEG, PNG ou WebP, até 2 MB.
    /// </summary>
    [HttpPut("me/picture")]
    [RequestSizeLimit(ProfilePictureFormat.MaxBytes + 64 * 1024)]
    [RequestFormLimits(MultipartBodyLengthLimit = ProfilePictureFormat.MaxBytes + 64 * 1024)]
    [ProducesResponseType(typeof(UserProfileDTO), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<UserProfileDTO>> UploadPicture(IFormFile? file, CancellationToken cancellationToken)
    {
        if (file is null || file.Length == 0)
            throw new EntityValidationException("picture", "A foto é obrigatória", ErrorCodes.INVALID_PROFILE_PICTURE);

        await using Stream stream = file.OpenReadStream();
        UserProfileDTO profile = await _profileService.SavePictureAsync(
            User.GetUserId(),
            stream,
            file.Length,
            cancellationToken);
        return Ok(profile);
    }

    /// <summary>
    /// Remove a foto de perfil do usuário autenticado.
    /// </summary>
    [HttpDelete("me/picture")]
    [ProducesResponseType(typeof(UserProfileDTO), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<UserProfileDTO>> DeletePicture(CancellationToken cancellationToken)
    {
        UserProfileDTO profile = await _profileService.RemovePictureAsync(User.GetUserId(), cancellationToken);
        return Ok(profile);
    }

    /// <summary>
    /// Imagem da foto de perfil. O acesso usa o token efêmero emitido em pictureUrl.
    /// </summary>
    [HttpGet("{id:guid}/picture")]
    [Authorize(AuthenticationSchemes = PictureAccessTokenDefaults.AuthenticationScheme)]
    [ProducesResponseType(typeof(FileResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetPicture(Guid id, CancellationToken cancellationToken)
    {
        UserPictureFile? picture = await _profileService.OpenPictureAsync(id, cancellationToken);
        if (picture is null)
            return NotFound();

        return File(picture.Content, picture.ContentType);
    }
}
