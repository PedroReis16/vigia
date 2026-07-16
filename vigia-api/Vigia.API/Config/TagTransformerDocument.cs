using Microsoft.OpenApi;
using Swashbuckle.AspNetCore.SwaggerGen;

namespace Vigia.API.Config;


public class TagDescriptionsDocumentFilter : IDocumentFilter
{
    public void Apply(OpenApiDocument swaggerDoc, DocumentFilterContext context)
    {
        swaggerDoc.Tags = new HashSet<OpenApiTag>();
    }
}