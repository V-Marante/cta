# Deployment and data-release guide

For routine releases after setup, follow the copy/paste [release runbook](release-runbook.md). It separates frontend-only, backend/container, Fly configuration, new SQLite extraction, asset, and mixed releases.

## Architecture and trust boundary

The frontend is a static Vite build for Cloudflare Pages. The public API runs on one auto-stopping Fly Machine. Its read-only SQLite file is copied into the image, so image and data are one immutable release. Versioned portraits are published separately to R2 (or another static host). Team Planner state remains in browser `localStorage`.

Extraction and importing are local-only. GitHub Actions never receives APKs, raw extraction trees, proprietary source assets, credentials, or the production database. This repository uses **Pattern C: prebuilt backend image**: the owner prepares and reviews public artifacts, builds and tests the image locally, pushes that exact image, and deploys it. CI uses only a generated synthetic database. There is no Fly volume and production never imports or mutates data.

## One-time manual setup checklist

### GitHub

- Create/select the repository; decide public versus private after reviewing all history and reports.
- Enable Actions, review Actions permissions, and optionally protect `main` with the three CI jobs required.
- Create a `production` environment with required reviewers for manual Fly deployment.
- If using the optional workflow, add environment secret `FLY_API_TOKEN`, scoped to the target app. Do not expose it to pull requests.
- Review logs/artifacts for sensitive paths. These workflows upload no generic artifacts.

### Fly.io

- Create an account and organization; install and authenticate `flyctl`.
- Choose a globally unique app name and replace the placeholder in `fly.toml`.
- Confirm `arn` (Stockholm) is available or choose a nearby region; run `fly apps create <name> --org <org>`.
- Authenticate Docker to Fly's registry, tag/push the locally approved image, and deploy that exact immutable tag.
- Set `AllowedOrigins__0=https://<frontend-domain>` as a Fly secret/runtime variable. Add further indexed origins only when required.
- Optionally configure an API custom domain and DNS. Verify TLS, `/health`, `/ready`, `/api/meta`, suspend/auto-start, zero minimum Machines, one shared CPU, 512 MB, and actual billing.

There is deliberately no volume. Adjust region, `shared-cpu-1x`, 512 MB, suspend behavior, zero minimum, or `/health` in `fly.toml` only after observing production needs.

### Cloudflare Pages

- Create an account and Pages project, connect GitHub, and select `web/cta-web` as root.
- Use `npm ci && npm run build`; output directory is `dist`.
- Set public build variables `VITE_API_URL=https://<api-domain>`, optional `VITE_ASSET_BASE_URL=https://<asset-domain>`, and `VITE_SHOW_FAN_DISCLAIMER=true`.
- Add a custom frontend domain, verify TLS, the `_redirects` SPA fallback, direct loads of `/heroes`, `/heroes/<id>`, `/team-planner`, and `/tier-list`, and cache headers. `index.html` is not immutable; hashed `/assets/*` files are.

Cloudflare Pages Git integration is preferred; no Cloudflare token is needed in GitHub. GitHub Pages is possible but history routing needs a 404-copy workaround or hash routing and a repository base path; it is not the documented primary target.

### Cloudflare R2 and DNS

- Create an R2 bucket and decide whether reviewed portraits will be public through a custom domain.
- Create a bucket-scoped upload token, never an account-wide token; keep credentials outside Git.
- Configure the asset domain, cache headers, optional lifecycle rules, and CORS only if browser/canvas access requires it.
- Upload only reviewed versioned paths such as `heroes/2026-08-06/<stable-id>.webp`; never overwrite prior versions or upload raw packages.
- Configure frontend, API, and asset DNS names; verify HTTPS. Update API CORS and rebuild the frontend with final public origins.

### Local machine

- Install Docker, Fly CLI, .NET 10 SDK, Node 24, Python 3.11+, SQLite support, and an R2-compatible uploader (`aws` CLI is used by the supplied script).
- Authenticate CLIs outside the repository. Keep extraction and proprietary inputs under ignored `samples/`, `extracted/`, and `local/proprietary/` paths.
- Copy `.env.example` values into an ignored shell/environment configuration. Never place secrets in frontend variables.
- Manually review the first public database and every portrait set before publication.

## Configuration

Backend variables use the existing flat .NET keys: `Database`, `GameId`, `AllowedOrigins__0`, `ApplicationVersion`, `Commit`, `DataImportId`, `GameVersion`, `DatabaseHash`, `AssetsVersion`, `PortraitMode`, and `PortraitPathTemplate`. Docker fixes `Database=/app/data/cta.sqlite`; production startup fails if it is missing/unreadable. Use portrait mode `external` for versioned hosted paths, `local` for API-served development PNGs, or `none` for placeholders only. `ASPNETCORE_URLS` is port 8080. `/health` checks the process; `/ready` opens SQLite read-only; `/api/meta` exposes only supplied non-sensitive release values.

Frontend `VITE_*` variables are public in JavaScript and must never contain secrets. `VITE_API_URL` is required in production. `VITE_ASSET_BASE_URL` moves API-provided relative portrait paths to an external origin; if unset, portraits use the API origin, and failed/missing portraits become text placeholders. Setting no portrait references in public data supports a portrait-free site.

CORS limits browser origins; it is not authentication and cannot make a public catalogue API private. Development defaults only to `http://localhost:5173`; production requires explicit origins. Forwarded headers are accepted for Fly's proxy, production errors are generic, console logs are structured JSON, and normal host shutdown is graceful.

## CI and normal deployments

Pull requests and pushes to `main` run importer/backend tests, frontend tests/build, and a production container smoke test using generated synthetic data. Workflows have read-only permissions, no `pull_request_target`, no secrets, no production artifacts, and no deployments.

Cloudflare Pages Git integration deploys reviewed frontend commits. Backend code changes require a new locally built image because the approved database must be included. The optional manual `deploy-fly-image.yml` accepts an already-pushed image reference, runs only from `main`, and should be protected by the production environment. It never builds/extracts data.

## Local data release

1. Perform BlueStacks extraction using the documented Windows PowerShell and `HD-Adb.exe` process; never Linux adb or hosted runners.
2. Import locally into `extracted/cta.sqlite` using the README command.
3. Run `./scripts/prepare-public-release.sh extracted/cta.sqlite`. It copies the DB, redacts local roots/source records, removes artifacts/diagnostics, vacuums it, writes a hash manifest, and runs allow-list validation.
4. Manually inspect `artifacts/public/cta.sqlite` and any selected portraits. The sanitizer is a technical safeguard, not a content/legal approval.
5. Put approved optimized/versioned portrait output under ignored `local/proprietary/public-assets/heroes/<assets-version>/`; create an asset manifest mapping stable IDs to paths.
6. Run `./scripts/release-local.sh`. This performs sanitization, all tests, image build, container readiness/API smoke tests, private-path inspection, and hashes. It performs no remote action.
7. Tag the tested image immutably, authenticate Docker to Fly, and push it to `registry.fly.io/<app>:<release>`.
8. Preview asset publication with `R2_DESTINATION=... R2_ENDPOINT_URL=... ./scripts/publish-assets.sh`; use `--execute` only after review and type the confirmation.
9. Preview Fly deployment with `FLY_APP_NAME=... FLY_IMAGE_REF=... ./scripts/deploy-fly-image.sh`; use `--execute` and type the confirmation.
10. Verify public `/health`, `/ready`, `/api/meta`, a hero query, frontend direct routes, portraits/placeholders, and expected data/assets versions.

`scripts/inspect-production-image.sh <tag>` lists `/app`; `smoke-test-image.sh` also exports the container and rejects obvious private directories. Remote actions are deliberately separate and confirmation-gated.

Local image builds use an empty temporary Docker configuration because they pull only public base images. This also avoids WSL failures caused by an unavailable `docker-credential-desktop.exe`. Set `CTA_USE_DOCKER_CONFIG=1` only if the build genuinely needs the caller's normal Docker authentication; pushing remains a separate manual operation.

## Public artifact validation

`validate-public-artifacts.sh` requires the exact `artifacts/public/cta.sqlite`, permits only named JSON manifests at the root and PNG/WebP/AVIF files under `portraits/`, rejects symlinks, unexpected files/formats, images over 5 MiB, a DB over 250 MiB, unexpected SQLite tables, failed `quick_check`, missing API tables, and obvious home paths/credential-like strings. It does not determine copyright status, verify factual accuracy, detect every secret, or decide whether names/text/art are appropriate to publish. Manual row/schema/content and visual review remains mandatory.

## Rollback

- **Backend:** identify a prior immutable Fly registry tag, run `flyctl deploy --app <app> --image <exact-tag>`, then verify `/health`, `/ready`, `/api/meta`, and the expected database hash/import version.
- **Frontend:** roll back in Pages deployment history or redeploy a known commit; check API compatibility and direct routes.
- **Assets:** retain versioned paths, restore the prior manifest/frontend asset version, and never rely on immediate CDN invalidation. Do not overwrite old release directories.

## Troubleshooting and cost controls

- Startup `Required SQLite database...`: prepare the artifact, check image `/app/data/cta.sqlite`, and ensure it is readable.
- `/ready` 503: inspect structured logs and validate SQLite locally; `/health` can remain 200 when DB readiness fails after startup.
- Browser CORS failure: set the exact scheme/host origin and restart the API. CORS does not fix DNS/TLS.
- Direct route 404: confirm `_redirects` is in Pages output.
- Missing portraits: check asset base/path/CORS; fallback is intentional and supports a no-portrait deployment.

Defaults minimize cost: one shared-CPU Fly Machine, 512 MB, suspend/auto-start, zero minimum, no volume/database service, static Pages, versioned R2 assets, no Workers/Functions, and no retained CI artifacts. Provider pricing and free tiers change; review both dashboards after first deployment.

## Proprietary-content and fan-site review

Personal or non-commercial use does not automatically grant redistribution rights, and a reachable fan site is public distribution. Names, portraits, icons, descriptions, and other game material may be protected by copyright or trademark. Limit assets to what identification/commentary needs; avoid original-resolution or complete dumps; do not imply publisher endorsement; keep a prompt takedown process; use placeholders if uncertain; and obtain legal advice if the project becomes commercial, popular, or disputed.

Suggested disclaimer (not a guarantee of lawful use):

> This is an unofficial fan-made project and is not affiliated with or endorsed by the game’s developer or publisher. Game names, artwork, icons, and related assets belong to their respective owners.

Before launch, review current publisher terms/fan-content policies, decide whether portraits will be published, avoid monetization until rights implications are understood, and document how rights-holder removal requests are handled.
