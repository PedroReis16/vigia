namespace Vigia.API.Models.DTOs.Users;

public record UpsertPushTokenDTO(string Token, string Platform);

public record DeletePushTokenDTO(string Token);
