using System.Reflection;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Mvc.ApplicationModels;
using Microsoft.OpenApi;
using Vigia.API.Config;
using Vigia.API.Contracts;
using Vigia.API.Hubs;
using Vigia.API.Services;
using Vigia.Database.Extensions;
using Vigia.Cache.Extensions;
using Vigia.API.Contracts.CacheServices;
using Vigia.API.Services.CacheServices;
using Vigia.Models.Contracts;
using Vigia.API.Contracts.Devices;
using Vigia.API.Services.Devices;
using Vigia.Models.Extensions;
using Vigia.Models.Middlewares;
using Vigia.Fiware.Extensions;
using Microsoft.AspNetCore.SignalR;
using Vigia.Cloud.Extensions;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

string basePath = builder.Configuration.GetValue<string>("BasePath") ?? string.Empty;

builder.Services.AddControllers(options =>
{
    options.Conventions.Add(new RouteTokenTransformerConvention(new SlugifyParameterTransformer()));
}).AddJsonOptions(options =>
{
    options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
});

// Database
builder.Services.AddPostgres(builder.Configuration.GetConnectionString("VigiaDb")!);

// Cache
builder.Services.AddRedisCache(builder.Configuration);

// Auth
builder.Services.ConfigureOAuth(builder.Configuration);

// Fiware
builder.Services.AddFiware(builder.Configuration);

// Middlewares
builder.Services.AddScoped<GlobalExceptionHandler>();
builder.Services.AddScoped<HttpResponseCacheHandler>();
builder.Services.AddTransient<ForwardingHandler>();
builder.Services.AddHttpContextAccessor();

// Cloud
builder.Services.AddCloudServices(builder.Configuration);

// Services
builder.Services.AddTransient<IUserService, UserService>();
builder.Services.AddTransient<IDevicesService, DevicesService>();
builder.Services.AddTransient<IDeviceUsersService, DeviceUsersService>();
builder.Services.AddTransient<IDeviceShareService, DeviceShareService>();
builder.Services.AddTransient<IAuthService, AuthService>();
builder.Services.AddTransient<IDeviceCommandsService, DeviceCommandsService>();
builder.Services.AddSingleton<IGroupRealtimeNotifier, GroupRealtimeNotifier>();
builder.Services.AddSingleton<IUserIdProvider, JwtUserIdProvider>();
builder.Services.AddTransient<IVersionService, VersionService>();
builder.Services.AddTransient<IAlertService, AlertService>();
builder.Services.AddSignalR();

builder.Services.AddSingleton<JwtConverterService>(); // Singleton para Encode e Decode de tokens JWT

// Repository Services
builder.Services.AddRepositoryServices();

// Cache Services
builder.Services.AddSingleton<IRevokedTokensCacheService, RevokedTokensCacheService>();
builder.Services.AddSingleton<IDeviceFrameCacheService, DeviceFrameCacheService>();
builder.Services.AddSingleton<IDeviceIdentityCacheService, DeviceIdentityCacheService>();
builder.Services.AddSingleton<IFrameAccessCacheService, FrameAccessCacheService>();

builder.Services.AddSingleton<IDeviceSignPublicKeyProvider, DeviceSignPublicKeyProvider>();
builder.Services.AddSingleton<IFrameAccessTokenProvider, FrameAccessTokenProvider>();

// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(option =>
{
    option.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        In = ParameterLocation.Header,
        Description = "OAuth 2.0 Access Token",
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        BearerFormat = "JWT",
        Scheme = "Bearer"
    });
    option.AddSecurityRequirement(document => new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecuritySchemeReference("Bearer", document),
            []
        }
    });
    var xmlFilename = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xmlFilename);
    option.DocumentFilter<TagDescriptionsDocumentFilter>();
    if (File.Exists(xmlPath))
    {
        option.IncludeXmlComments(xmlPath);
    }
});

WebApplication app = builder.Build();

// app.ConfigureRequestLogging();

app.UseSwagger(c =>
{
    c.PreSerializeFilters.Add((swagger, httpReq) =>
    {
        var scheme = app.Environment.IsProduction() ? "https" : "http";
        swagger.Servers = [new OpenApiServer { Url = $"{scheme}://{httpReq.Host.Value}/{basePath}" }];
    });
    c.RouteTemplate = basePath + "/swagger/{documentName}/swagger.json";
});
app.UseSwaggerUI(options =>
{
    options.SwaggerEndpoint($"/{basePath}/swagger/v1/swagger.json", "GeoCidadao.GerenciamentoPostsAPI v1");
    options.RoutePrefix = $"{basePath}/swagger";
});

// Aplicação dos middlewares
app.UseMiddleware<GlobalExceptionHandler>();
app.UseMiddleware<HttpResponseCacheHandler>();

app.UsePathBase($"/{basePath}");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
app.MapHub<DeviceGroupsHub>("/hubs/device-groups");

app.Run();
