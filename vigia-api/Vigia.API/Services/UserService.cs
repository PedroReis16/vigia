using System.ComponentModel.DataAnnotations;
using Vigia.API.Contracts;
using Vigia.Database.Contracts;
using Vigia.API.Models.DTOs.Auth;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;
using Vigia.Models.Extensions;
using Vigia.Models.Helpers;

namespace Vigia.API.Services;

internal class UserService(ILogger<UserService> logger, IServiceScopeFactory scopeFactory) : IUserService
{
    private readonly ILogger<UserService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;


    public async Task RegisterNewUserAsync(NewUserDTO newUserDTO)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            IUserDao userDao = scope.ServiceProvider.GetRequiredService<IUserDao>();

            byte[] passwordSalt = PasswordHasher.GenerateSalt();
            byte[] passwordHash = PasswordHasher.Hash(newUserDTO.Password, passwordSalt);

            ValidateNewUser(newUserDTO);

            Guid newUserId = Guid.NewGuid();

            Group newUserGroup = new()
            {
                OwnerId = newUserId,
            };

            User newUser = new()
            {
                Name = newUserDTO.Name,
                Email = newUserDTO.Email,
                Password = passwordHash,
                Salt = passwordSalt,
                LinkedGroups = new List<Group> { newUserGroup }
            };

            await userDao.AddAsync(newUser);

            _logger.LogInformation($"Novo usuário registrado com sucesso");
        }
        catch (EntityValidationException) { throw; }
        catch (Exception ex)
        {
            string errorMessage = $"Houve um erro ao tentar registrar um novo usuário com o email {newUserDTO.Email}: {ex.GetFullMessage()}";
            _logger.LogError(errorMessage);
            throw new Exception(errorMessage);
        }
    }

    private void ValidateNewUser(NewUserDTO newUserDTO)
    {
        if (string.IsNullOrWhiteSpace(newUserDTO.Name))
            throw new EntityValidationException(nameof(newUserDTO.Name), "O nome do usuário é obrigatório", ErrorCodes.USER_NAME_IS_REQUIRED);
        if (string.IsNullOrWhiteSpace(newUserDTO.Email))
            throw new EntityValidationException(nameof(newUserDTO.Email), "O email do usuário é obrigatório", ErrorCodes.USER_EMAIL_IS_REQUIRED);
        if (!new EmailAddressAttribute().IsValid(newUserDTO.Email))
            throw new EntityValidationException(nameof(newUserDTO.Email), "O email do usuário não é válido", ErrorCodes.INVALID_EMAIL);
        if (string.IsNullOrWhiteSpace(newUserDTO.Password))
            throw new EntityValidationException(nameof(newUserDTO.Password), "A senha do usuário é obrigatória", ErrorCodes.USER_PASSWORD_IS_REQUIRED);
    }

    
}