# Unified Fly.io deployment

## Architecture

One locally built Docker image contains the published ASP.NET Core API, compiled React/Vite frontend, reviewed versioned portraits and UI icons, and a purpose-built SQLite catalogue. ASP.NET Core serves `/api/*`, the SPA, and `/assets/*` from one Fly.io origin. The database is `/app/data/cta.sqlite`, mode `0444`, and every application connection uses SQLite read-only mode. There is no Fly volume.

Team Planner and tier-list state remain browser-local. GitHub contains source plus synthetic test inputs only. Production extraction, data, and proprietary assets stay local and ignored. Cloudflare Pages and R2 are not runtime dependencies; equivalent SPA routing, security headers, and cache policy now live in ASP.NET Core.

## Local production inputs

Run `CTA_ASSETS_VERSION=<immutable-version> ./scripts/prepare-release.sh` after producing and reviewing the public database and application-ready assets. It creates this ignored tree:

```text
local-release/
├── data/
│   ├── cta.sqlite
│   └── import-manifest.json
└── assets/
    ├── heroes/<assets-version>/<hero-id>.png
    └── ui-icons/<assets-version>/
        ├── jobs/<job-id>.png
        └── elements/<element-id>.png
```

Defaults are `SOURCE_DATABASE=extracted/cta.sqlite`, `HERO_ASSET_SOURCE=local/proprietary/hero-icons`, and `UI_ASSET_SOURCE=local/proprietary/ui-icons`; each can be overridden. `local-release/` is ignored by Git but deliberately included in the Docker context. Do not put secrets there. Production builds validate the database and non-empty asset directories before Docker runs and again inside the build.

## Build modes and verification

Synthetic CI requires no private input:

```bash
./scripts/verify.sh
docker build --target runtime --build-arg RELEASE_MODE=synthetic -t cta:synthetic .
RELEASE_IMAGE=cta:synthetic ./scripts/smoke-test-image.sh
```

The Docker preparation stage generates a minimal synthetic public-schema database and placeholder PNGs. CI tests the generator, frontend, backend, unified image, and running container without secrets.

Production preparation and exact-image testing:

```bash
export CTA_ASSETS_VERSION=YYYY-MM-DD
export RELEASE_IMAGE=registry.fly.io/<app>:YYYY-MM-DD-<git-sha>
export VCS_REF=<git-sha>
./scripts/prepare-release.sh
./scripts/release-local.sh
./scripts/inspect-production-image.sh "$RELEASE_IMAGE"
```

Individual verification commands:

```bash
npm ci --prefix web/cta-web
npm test --prefix web/cta-web
npm run build --prefix web/cta-web
dotnet test api/Cta.Api.Tests/Cta.Api.Tests.csproj --configuration Release
dotnet publish api/Cta.Api/Cta.Api.csproj --configuration Release --output /tmp/cta-publish
./scripts/build-production-image.sh
RELEASE_IMAGE="$RELEASE_IMAGE" ./scripts/smoke-test-image.sh
PORT=8080 RELEASE_IMAGE="$RELEASE_IMAGE" ./scripts/run-release-image.sh
curl -f http://localhost:8080/
curl -f 'http://localhost:8080/api/heroes?pageSize=1'
curl -f "http://localhost:8080/assets/heroes/$CTA_ASSETS_VERSION/<hero-id>.png"
curl -f "http://localhost:8080/assets/ui-icons/$CTA_ASSETS_VERSION/jobs/brawler.png"
```

The local runner uses a read-only container filesystem and temporary `/tmp`. The smoke test verifies health/readiness, API/database reads, `/`, a direct SPA route, a portrait, UI icons, missing-asset/API 404s, and absence of raw private paths.

## Manual Pattern C deployment

1. Prepare and review local production data/assets.
2. Run all verification.
3. Build one immutable production image.
4. Run and test that exact tag locally.
5. Authenticate outside the repository: `flyctl auth docker`.
6. Push the exact tag: `docker push "$RELEASE_IMAGE"`.
7. Deploy it: `FLY_APP_NAME=<app> FLY_IMAGE_REF="$RELEASE_IMAGE" ./scripts/deploy-fly-image.sh --execute`.
8. Verify `/`, direct SPA routes, `/health`, `/ready`, `/api/meta`, `/api/heroes`, and representative assets on Fly.

Steps 5–7 are intentionally manual. `fly.toml` has no hard-coded app name. The retained manual GitHub Fly workflow deploys only a caller-supplied, previously approved image.

Rollback means redeploying a previous immutable tag or digest. Code, frontend, database, and assets roll back together.

## Caching and security

Versioned `/assets/*` (including Vite hashed files) receive one-year immutable caching; `index.html` and SPA fallbacks receive `no-cache`. Missing `/assets/*` and `/api/*` return 404. Directory browsing and uploads are not enabled. Forwarded headers, generic production errors, security headers, a non-root user, and read-only SQLite are preserved. Same-origin hosting removes production CORS configuration. Vite's existing production default emits no source maps. The runtime contains neither Node nor the .NET SDK.

## Cloudflare retirement

Only after the unified Fly deployment is verified, the owner may manually remove the old Cloudflare Pages project, R2 bucket/custom asset domain, Pages/R2 DNS records, and R2 upload token. Do not remove them before replacement verification. No repository command changes Cloudflare resources.
