using System.Reflection;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Mvc.ApplicationModels;
using Microsoft.OpenApi;
using Vigia.API.Config;
using Vigia.API.Contracts;
using Vigia.API.Services;
using Vigia.Models.Middlewares;
using Vigia.Database.Extensions;
using Vigia.Cache.Extensions;
using Vigia.API.Database.Contracts;
using Vigia.API.Database.EFDao;

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
builder.Services.AddInMemoryCache(builder.Configuration);


// Middlewares 

builder.Services.AddTransient<GlobalExceptionHandler>();
builder.Services.AddTransient<HttpResponseCacheHandler>();
builder.Services.AddHttpContextAccessor();

// Services
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<IDeviceService, DeviceService>();

// Dao Services
builder.Services.AddTransient<IDevicesDao, DevicesDao>();

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

app.UseMiddleware<GlobalExceptionHandler>();

app.UseMiddleware<HttpResponseCacheHandler>();

app.UsePathBase($"/{basePath}");


app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();
