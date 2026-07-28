using Microsoft.AspNetCore.Mvc;

namespace Vigia.API.Controllers;

public class UserController(IServiceScopeFactory scopeFactory) : ControllerBase
{
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;


}