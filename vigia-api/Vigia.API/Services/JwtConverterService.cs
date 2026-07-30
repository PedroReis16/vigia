using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.IdentityModel.Tokens;

namespace Vigia.API.Services;

public class JwtConverterService(IConfiguration configuration)
{
    private readonly IConfiguration _configuration = configuration;

    private (string SecretKey, int ExpiresIn, string Issuer, string Audience, int RefreshTokenExpiresIn) GetJwtSettings() => (
        _configuration.GetValue<string>("JWT:SecretKey")!,
        _configuration.GetValue<int>("JWT:ExpiresIn"),
        _configuration.GetValue<string>("JWT:Issuer")!,
        _configuration.GetValue<string>("JWT:Audience")!,
        _configuration.GetValue<int>("JWT:RefreshTokenExpiresIn")
    );

    public string Encode(Guid userId, List<string> roles)
    {
        // Mapear as claims do usuário
        var claims = new List<Claim>{
            new(JwtRegisteredClaimNames.Sub, userId.ToString()),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
        };

        roles.ForEach(role => claims.Add(new("role", role)));

        // Configurar chave e algoritmo de assinatura
        var tokenKey = Encoding.UTF8.GetBytes(GetJwtSettings().SecretKey);
        var symmetricKey = new SymmetricSecurityKey(tokenKey);
        var creds = new SigningCredentials(symmetricKey, SecurityAlgorithms.HmacSha256Signature);

        var jwtSettings = GetJwtSettings();

        // Definir limitações do token
        var tokenDescriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(claims),
            Expires = DateTime.UtcNow.AddSeconds(jwtSettings.ExpiresIn),
            SigningCredentials = creds,
            Issuer = jwtSettings.Issuer,
            Audience = jwtSettings.Audience,
        };

        // Criar o token
        var tokenHandler = new JwtSecurityTokenHandler();
        var token = tokenHandler.CreateToken(tokenDescriptor);

        return tokenHandler.WriteToken(token);
    }


    public bool Decode(string token, out (Guid tokenId, DateTime expiresAt, Guid userId, List<string> roles)? decodedProperies)
    {
        try
        {
            var tokenHandler = new JwtSecurityTokenHandler();

            var jwtSettings = GetJwtSettings();

            tokenHandler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSettings.SecretKey)),
                ValidateIssuer = true,
                ValidIssuer = jwtSettings.Issuer,
                ValidateAudience = true,
                ValidAudience = jwtSettings.Audience,
                ValidateLifetime = true,
                ClockSkew = TimeSpan.FromSeconds(30),
            }, out SecurityToken? validatedToken);


            var decodedToken = tokenHandler.ReadJwtToken(token);

            var tokenIdClaim = decodedToken.Claims.FirstOrDefault(c => c.Type == JwtRegisteredClaimNames.Jti)!.Value;
            var expiresAtClaim = decodedToken.Claims.FirstOrDefault(c => c.Type == JwtRegisteredClaimNames.Exp)!.Value;
            var userIdClaim = decodedToken.Claims.FirstOrDefault(c => c.Type == JwtRegisteredClaimNames.Sub)!.Value;
            var rolesClaim = decodedToken.Claims.Where(c => c.Type == "role").Select(c => c.Value).ToList();

            decodedProperies = (
                Guid.Parse(tokenIdClaim),
                DateTime.UnixEpoch.AddSeconds(double.Parse(expiresAtClaim)),
                Guid.Parse(userIdClaim),
                rolesClaim
            );

            return true;
        }
        catch (Exception)
        {
            decodedProperies = null;
            return false;
        }
    }
}