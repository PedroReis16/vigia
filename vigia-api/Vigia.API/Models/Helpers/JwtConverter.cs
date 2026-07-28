using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.AspNetCore.StaticAssets;
using Microsoft.IdentityModel.Tokens;
using Vigia.API.Models.DTOs.Auth;

namespace Vigia.API.Models.Helpers;

public static class JwtConverter
{
    private static (string SecretKey, int ExpiresIn, string Issuer, string Audience) GetJwtSettings(IConfiguration configuration) => (
        configuration.GetValue<string>("JWT:SecretKey")!,
        configuration.GetValue<int>("JWT:ExpiresIn"),
        configuration.GetValue<string>("JWT:Issuer")!,
        configuration.GetValue<string>("JWT:Audience")!
    );

    public static string Encode(IConfiguration configuration, Guid userId, List<string> roles)
    {
        // Mapear as claims do usuário
        var claims = new List<Claim>{
            new(JwtRegisteredClaimNames.Sub, userId.ToString()),
            new(ClaimTypes.Role, string.Join(",", roles)),
        };

        // Configurar chave e algoritmo de assinatura
        var tokenKey = Encoding.UTF8.GetBytes(GetJwtSettings(configuration).SecretKey);
        var symmetricKey = new SymmetricSecurityKey(tokenKey);
        var creds = new SigningCredentials(symmetricKey, SecurityAlgorithms.HmacSha256Signature);

        // Definir limitações do token
        var tokenDescriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(claims),
            Expires = DateTime.UtcNow.AddSeconds(configuration.GetValue<int>("JWT:ExpiresIn")),
            SigningCredentials = creds,
            Issuer = configuration.GetValue<string>("JWT:Issuer"),
            Audience = configuration.GetValue<string>("JWT:Audience"),
        };

        // Criar o token
        var tokenHandler = new JwtSecurityTokenHandler();
        var token = tokenHandler.CreateToken(tokenDescriptor);

        return tokenHandler.WriteToken(token);
    }

    public static (Guid userId, List<string> roles) Decode(string token)
    {
        var tokenHandler = new JwtSecurityTokenHandler();

        var securityToken = tokenHandler.ReadJwtToken(token);

        var idClaim = securityToken.Claims.FirstOrDefault(c => c.Type == JwtRegisteredClaimNames.Sub)?.Value;
        var nameClaim = securityToken.Claims.FirstOrDefault(c => c.Type == ClaimTypes.Name)?.Value;
        var emailClaim = securityToken.Claims.FirstOrDefault(c => c.Type == ClaimTypes.Email)?.Value;
        var rolesClaim = securityToken.Claims.Where(c => c.Type == ClaimTypes.Role).Select(c => c.Value).ToList();


        // 3. Reconstrói e retorna o objeto original
        return (
            idClaim != null ? Guid.Parse(idClaim) : Guid.Empty,
            rolesClaim ?? []
        );
    }
}