# syntax=docker/dockerfile:1.7
FROM node:24-alpine AS frontend
WORKDIR /src/web/cta-web
COPY web/cta-web/package.json web/cta-web/package-lock.json ./
RUN npm ci
COPY web/cta-web/ ./
ARG ASSETS_VERSION=synthetic
ENV VITE_ASSETS_VERSION=$ASSETS_VERSION
RUN npm run build

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS backend
WORKDIR /src
COPY api/Cta.Api/Cta.Api.csproj api/Cta.Api/
RUN dotnet restore api/Cta.Api/Cta.Api.csproj
COPY api/Cta.Api/ api/Cta.Api/
RUN dotnet publish api/Cta.Api/Cta.Api.csproj -c Release --no-restore -o /out /p:UseAppHost=false

FROM python:3.13-alpine AS release-inputs
ARG RELEASE_MODE=synthetic
ARG ASSETS_VERSION=synthetic
WORKDIR /prepare
COPY scripts/create-synthetic-public-db.py /prepare/create-synthetic-public-db.py
COPY local-release/ /prepare/local-release/
RUN set -eu; \
    case "$RELEASE_MODE" in \
      synthetic) \
        mkdir -p /bundle/data /bundle/assets/heroes/$ASSETS_VERSION \
          /bundle/assets/ui-icons/$ASSETS_VERSION/jobs /bundle/assets/ui-icons/$ASSETS_VERSION/elements; \
        python3 /prepare/create-synthetic-public-db.py /bundle/data/cta.sqlite; \
        printf '\211PNG\r\n\032\n\000\000\000\rIHDR\000\000\000\001\000\000\000\001\010\006\000\000\000\037\025\304\211\000\000\000\rIDAT\010\327c\370\317\300\360\037\000\005\376\001\376\334\314Y\347\000\000\000\000IEND\256B\140\202' > /bundle/assets/heroes/$ASSETS_VERSION/SyntheticHero.png; \
        cp /bundle/assets/heroes/$ASSETS_VERSION/SyntheticHero.png /bundle/assets/ui-icons/$ASSETS_VERSION/jobs/brawler.png; \
        cp /bundle/assets/heroes/$ASSETS_VERSION/SyntheticHero.png /bundle/assets/ui-icons/$ASSETS_VERSION/elements/fire.png ;; \
      production) \
        test -f /prepare/local-release/data/cta.sqlite || { echo 'Production release input missing: local-release/data/cta.sqlite' >&2; exit 1; }; \
        python3 -c 'import sqlite3; db=sqlite3.connect("file:/prepare/local-release/data/cta.sqlite?mode=ro", uri=True); required={"release_info","catalog_entities","catalog_text","catalog_relations"}; actual={r[0] for r in db.execute("select name from sqlite_master where type=?", ("table",))}; assert required <= actual, "Production SQLite database does not have the required public schema"'; \
        test -d /prepare/local-release/assets/heroes/$ASSETS_VERSION || { echo "Production hero asset directory missing: local-release/assets/heroes/$ASSETS_VERSION" >&2; exit 1; }; \
        test -d /prepare/local-release/assets/ui-icons/$ASSETS_VERSION/jobs || { echo "Production job icon directory missing: local-release/assets/ui-icons/$ASSETS_VERSION/jobs" >&2; exit 1; }; \
        test -d /prepare/local-release/assets/ui-icons/$ASSETS_VERSION/elements || { echo "Production element icon directory missing: local-release/assets/ui-icons/$ASSETS_VERSION/elements" >&2; exit 1; }; \
        find /prepare/local-release/assets/heroes/$ASSETS_VERSION -type f -name '*.png' -print -quit | grep -q . || { echo 'Production hero asset directory contains no PNG files' >&2; exit 1; }; \
        mkdir -p /bundle/data /bundle/assets; \
        cp /prepare/local-release/data/cta.sqlite /bundle/data/cta.sqlite; \
        cp -R /prepare/local-release/assets/. /bundle/assets/ ;; \
      *) echo "Invalid RELEASE_MODE: $RELEASE_MODE (expected synthetic or production)" >&2; exit 1 ;; \
    esac

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
ARG APPLICATION_VERSION=0.1.0
ARG VCS_REF=unknown
ARG DATA_IMPORT_ID=unknown
ARG GAME_VERSION=unknown
ARG DATABASE_HASH=unknown
ARG ASSETS_VERSION=synthetic
LABEL org.opencontainers.image.title="Crush Them All companion application" \
      org.opencontainers.image.version=$APPLICATION_VERSION \
      org.opencontainers.image.revision=$VCS_REF
WORKDIR /app
COPY --from=backend /out/ ./
COPY --from=frontend /src/web/cta-web/dist/ /app/wwwroot/
COPY --from=release-inputs /bundle/data/cta.sqlite /app/data/cta.sqlite
COPY --from=release-inputs /bundle/assets/ /app/wwwroot/assets/
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
    PortraitMode=bundled
EXPOSE 8080
ENTRYPOINT ["dotnet", "Cta.Api.dll"]
