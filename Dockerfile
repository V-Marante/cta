# syntax=docker/dockerfile:1.7
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY api/Cta.Api/Cta.Api.csproj api/Cta.Api/
RUN dotnet restore api/Cta.Api/Cta.Api.csproj
COPY api/Cta.Api/ api/Cta.Api/
RUN dotnet publish api/Cta.Api/Cta.Api.csproj -c Release --no-restore -o /out /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
ARG PUBLIC_DATABASE=artifacts/public/cta.sqlite
ARG APPLICATION_VERSION=0.1.0
ARG VCS_REF=unknown
ARG DATA_IMPORT_ID=unknown
ARG GAME_VERSION=unknown
ARG DATABASE_HASH=unknown
ARG ASSETS_VERSION=unknown
ARG PORTRAIT_MODE=none
LABEL org.opencontainers.image.title="Crush Them All catalogue API" \
      org.opencontainers.image.version=$APPLICATION_VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.source="https://github.com/OWNER/REPOSITORY"
WORKDIR /app
COPY --from=build /out/ ./
COPY ${PUBLIC_DATABASE} /app/data/cta.sqlite
RUN chown -R app:app /app && chmod 0444 /app/data/cta.sqlite
USER app
ENV ASPNETCORE_URLS=http://0.0.0.0:8080 \
    ASPNETCORE_ENVIRONMENT=Production \
    Database=/app/data/cta.sqlite \
    ApplicationVersion=$APPLICATION_VERSION \
    Commit=$VCS_REF \
    DataImportId=$DATA_IMPORT_ID \
    GameVersion=$GAME_VERSION \
    DatabaseHash=$DATABASE_HASH \
    AssetsVersion=$ASSETS_VERSION \
    PortraitMode=$PORTRAIT_MODE
EXPOSE 8080
ENTRYPOINT ["dotnet", "Cta.Api.dll"]
