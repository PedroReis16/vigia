# Build Vigia.API (.NET) — context = monorepo root
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Project files first (restore cache)
COPY vigia-api/Vigia.API/Vigia.API.csproj Vigia.API/
COPY vigia-api/Libraries/Vigia.Models/Vigia.Models.csproj Libraries/Vigia.Models/
COPY vigia-api/Libraries/Vigia.Database/Vigia.Database.csproj Libraries/Vigia.Database/
COPY vigia-api/Libraries/Vigia.Cache/Vigia.Cache.csproj Libraries/Vigia.Cache/
COPY vigia-api/Libraries/Vigia.Fiware/Vigia.Fiware.csproj Libraries/Vigia.Fiware/

RUN dotnet restore Vigia.API/Vigia.API.csproj

COPY vigia-api/Vigia.API/ Vigia.API/
COPY vigia-api/Libraries/ Libraries/

RUN dotnet publish Vigia.API/Vigia.API.csproj \
    -c Release \
    -o /app/publish \
    /p:UseAppHost=false

# Runtime
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

RUN mkdir -p /versions

ENV ASPNETCORE_URLS=http://+:8080 \
    versionPath=/versions/

COPY --from=build /app/publish .

EXPOSE 8080
ENTRYPOINT ["dotnet", "Vigia.API.dll"]
