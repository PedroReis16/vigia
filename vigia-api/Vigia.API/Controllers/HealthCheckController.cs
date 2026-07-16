using Microsoft.AspNetCore.Mvc;

namespace Vigia.API.Controllers;

[ApiController]
[Route("[controller]")]
public class HealthCheckController : ControllerBase
{
    [HttpGet]
    public IActionResult Get()
    {
        return Ok(new { message = "Vigia, cuidar de quem você ama nunca foi tão fácil" });
    }
}