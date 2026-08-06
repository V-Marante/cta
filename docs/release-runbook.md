# Release runbook

Use this guide after the one-time provider setup in [deployment.md](deployment.md). It covers routine releases and starts with the smallest safe flow for each kind of change.

No release command extracts data automatically. No validation command uploads or deploys anything. Commands that publish or deploy are separate and confirmation-gated.

## 1. Identify what changed

| Change | Frontend deploy | New backend image | New public SQLite | Asset upload | Fly config deploy |
|---|---:|---:|---:|---:|---:|
| Frontend code, CSS, `_headers`, `_redirects`, or `VITE_*` values | Yes | No | No | No | No |
| Backend/API code or backend configuration | No | Yes | No | No | No |
| `Dockerfile` or `.dockerignore` | No | Yes | No | No | No |
| `fly.toml` only | No | Usually no | No | No | Yes |
| New extraction/imported SQLite | Usually no | Yes | Yes | Maybe | No |
| New or changed portraits/icons | Maybe | No | No | Yes | No |
| API contract used by the frontend | Yes | Yes | Usually no | No | No |
| Dependency or shared CI/release scripts | Run all validation; deploy only affected applications | Depends | No | No | Depends |

When uncertain, use the mixed-release flow at the end. A backend image always includes an approved SQLite database, even when only backend code changed.

## 2. Common pre-release checks

Run these before every release:

```bash
git status --short
git diff --check
./scripts/verify.sh
```

Review the diff and confirm that no extracted files, generated databases, credentials, or proprietary binaries are tracked or staged:

```bash
git check-ignore local/proprietary/ artifacts/public/cta.sqlite
git diff --cached --name-only
```

For a normal reviewed release, record the source revision:

```bash
git rev-parse --short=7 HEAD
```

Do not release from an unexplained dirty working tree. The scripts warn about changes but cannot decide whether they are intentional.

## 3. Choose immutable versions and tags

Choose a release date/version and record the current commit:

```bash
export RELEASE_DATE="YYYY-MM-DD"
export GIT_SHA="$(git rev-parse --short=7 HEAD)"
export FLY_APP_NAME="your-actual-fly-app-name"
export RELEASE_IMAGE="registry.fly.io/${FLY_APP_NAME}:${RELEASE_DATE}-${GIT_SHA}"
export APPLICATION_VERSION="0.1.0"
export VCS_REF="$GIT_SHA"
```

For a data release, also set:

```bash
export CTA_GAME_VERSION="x.y.z"
export CTA_ASSETS_VERSION="$RELEASE_DATE"
export DATA_IMPORT_ID="the-reviewed-import-id"
```

Tags must be immutable. Never reuse or overwrite an existing release tag. Avoid `latest` because it makes rollback and database identification ambiguous.

## 4. Frontend-only release

Use this for React/TypeScript/CSS changes, static headers/redirects, or changed public `VITE_*` configuration.

1. Test and build with harmless production-style origins:

   ```bash
   npm ci --prefix web/cta-web
   npm test --prefix web/cta-web
   VITE_API_URL="https://api.example.com" \
   VITE_ASSET_BASE_URL="https://assets.example.com" \
   npm run build --prefix web/cta-web
   ```

2. Review `web/cta-web/dist/`. Confirm `_headers` and `_redirects` are present.
3. Merge/push the reviewed commit normally.
4. Let Cloudflare Pages Git integration build and deploy it. No Docker/Fly action is needed.
5. In Pages, verify the configured production variables are public values, not secrets.
6. Smoke test `/heroes`, a hero detail route, `/team-planner`, `/tier-list`, API requests, and portrait fallback behavior.
7. If it fails, roll back through Cloudflare Pages deployment history or redeploy the prior known commit.

Rebuild the frontend whenever its API base URL, asset base URL, or API contract changes because Vite embeds those values at build time.

## 5. Backend code, Dockerfile, or backend container release

Use this for API code, .NET dependencies/configuration, `Dockerfile`, or `.dockerignore` changes. Even code-only images require the currently approved public database.

1. Confirm `artifacts/public/cta.sqlite` is the approved current database. If absent, recreate it from the reviewed local database:

   ```bash
   ./scripts/prepare-public-release.sh extracted/cta.sqlite
   ```

2. Set the immutable image variables from section 3. Keep the existing data metadata values when the data did not change.
3. Run the complete local release validation:

   ```bash
   ./scripts/release-local.sh
   ```

   This prepares/validates public artifacts again, runs all tests, builds `RELEASE_IMAGE`, starts it, checks health/readiness/meta/API responses, inspects its filesystem, and prints hashes. It does not upload or deploy.

4. Verify the exact metadata before pushing:

   ```bash
   docker image inspect "$RELEASE_IMAGE" --format '{{json .Config.Labels}}'
   ./scripts/inspect-production-image.sh "$RELEASE_IMAGE"
   ```

5. Authenticate and push the exact tested tag:

   ```bash
   flyctl auth docker
   docker push "$RELEASE_IMAGE"
   ```

6. Preview and then explicitly deploy that tag:

   ```bash
   FLY_IMAGE_REF="$RELEASE_IMAGE" ./scripts/deploy-fly-image.sh
   FLY_IMAGE_REF="$RELEASE_IMAGE" ./scripts/deploy-fly-image.sh --execute
   ```

7. Verify production:

   ```bash
   curl --fail "https://api.example.com/health"
   curl --fail "https://api.example.com/ready"
   curl --fail "https://api.example.com/api/meta"
   curl --fail "https://api.example.com/api/heroes?pageSize=1"
   ```

8. Confirm `/api/meta` reports the intended commit and database hash. Roll back by deploying the prior immutable image tag if needed.

`build-production-image.sh` uses an isolated Docker configuration for public base-image pulls. `flyctl auth docker` and `docker push` are deliberately separate and use your normal Docker authentication.

## 6. `fly.toml`-only release

Use this for Machine size, memory, region, health checks, auto-start/stop, or other Fly runtime configuration.

1. Read the Fly diff carefully. Confirm there is still no volume and the internal port remains compatible with the image.
2. Validate the currently deployed image locally if there is any doubt:

   ```bash
   RELEASE_IMAGE="the-local-or-pulled-existing-tag" ./scripts/smoke-test-image.sh
   ```

3. Run a dry-run/config review with the Fly CLI where supported:

   ```bash
   flyctl config validate
   flyctl deploy --ha=false --build-only
   ```

   Do not accept a newly built image for a config-only release. The intended deployment should reference the already approved image.

4. Identify the exact currently approved registry image tag, then deploy it while applying the new configuration:

   ```bash
   export FLY_IMAGE_REF="registry.fly.io/<app>:<existing-approved-tag>"
   FLY_IMAGE_REF="$FLY_IMAGE_REF" ./scripts/deploy-fly-image.sh
   FLY_IMAGE_REF="$FLY_IMAGE_REF" ./scripts/deploy-fly-image.sh --execute
   ```

5. Verify `/health`, `/ready`, `/api/meta`, Machine count, region, memory, auto-stop behavior, and billing settings.

If a `fly.toml` change must accompany new backend code, follow the backend flow instead and deploy the new tested image once.

## 7. New extraction and SQLite data release

This is the highest-review flow. Extraction stays on the local developer machine.

1. Perform the BlueStacks extraction using Windows PowerShell and BlueStacks `HD-Adb.exe` as documented in the extraction reports. Never use Linux adb or a hosted runner.
2. Keep original packages and raw output under ignored private directories. Do not move them into `artifacts/public/`.
3. Import into the local SQLite database:

   ```bash
   PYTHONPATH=src python3 -m cta_importer import \
     samples/bluestacks/shared-data/cache/content \
     extracted/cta.sqlite \
     --game-id com.godzilab.idlerpg \
     --version "$CTA_GAME_VERSION"
   ```

4. Run the importer audits described in the README and investigate new warnings, missing localization, classification changes, and schema changes.
5. Prepare the sanitized public database:

   ```bash
   ./scripts/prepare-public-release.sh extracted/cta.sqlite
   ```

6. Manually inspect the public artifact before building:

   ```bash
   ./scripts/validate-public-artifacts.sh artifacts/public
   sqlite3 artifacts/public/cta.sqlite '.tables'
   sqlite3 artifacts/public/cta.sqlite 'PRAGMA quick_check;'
   sha256sum artifacts/public/cta.sqlite artifacts/public/import-manifest.json
   ```

   Confirm local paths are redacted, diagnostics/raw packages are absent, and only intended public data remains. Validation cannot make the legal/content publication decision.

7. Choose a new immutable image tag, even if backend code did not change. Set data metadata from section 3.
8. Run, review, and build locally:

   ```bash
   ./scripts/release-local.sh
   ```

9. If portraits also changed, complete the asset flow in section 8 before deploying the frontend that references the new asset version.
10. Push and deploy the exact image using steps 5–8 of the backend flow.
11. Confirm `/api/meta` reports the new import ID, game version, database hash, and assets version as applicable. Compare hero counts and representative heroes with the reviewed local data.

Never upload `extracted/cta.sqlite` directly. Only the sanitized `artifacts/public/cta.sqlite` may enter the image.

## 8. Portrait or static proprietary asset release

Use this only after deciding the selected assets are appropriate to publish.

1. Generate/optimize locally under the ignored directory:

   ```text
   local/proprietary/public-assets/heroes/<assets-version>/<stable-id>.webp
   ```

2. Keep the previous version directory unchanged. Do not overwrite existing CDN paths.
3. Generate and manually review an asset manifest mapping stable IDs to versioned paths.
4. Check formats, dimensions, sizes, hashes, provenance, and that no original packages or complete dumps are included.
5. Preview publication:

   ```bash
   export PUBLIC_ASSET_DIR="local/proprietary/public-assets"
   export R2_DESTINATION="s3://<bucket>/heroes/$CTA_ASSETS_VERSION"
   export R2_ENDPOINT_URL="https://<account>.r2.cloudflarestorage.com"
   ./scripts/publish-assets.sh
   ```

6. Publish only after review and explicit confirmation:

   ```bash
   ./scripts/publish-assets.sh --execute
   ```

7. Verify representative URLs, MIME types, CORS if needed, and immutable cache headers.
8. Configure the backend image with `CTA_PORTRAIT_MODE=external` and the matching `CTA_ASSETS_VERSION`, then follow the backend flow. Rebuild the frontend only if `VITE_ASSET_BASE_URL` or manifest/version selection embedded in it changed.
9. Roll back by restoring the previous manifest/assets version. Do not depend on immediate CDN invalidation.

## 9. API contract or mixed frontend/backend release

Use this when frontend and backend must change together, when a data release changes fields expected by the frontend, or when several categories above overlap.

1. Decide compatibility and deployment order:

   - Prefer backward-compatible API changes.
   - If the old frontend works with the new backend, deploy backend first, verify it, then deploy frontend.
   - If the new frontend works with the old backend, frontend may go first.
   - If neither direction is compatible, add a compatibility phase instead of relying on simultaneous deployments.

2. Prepare and review any new database/assets first.
3. Run the complete verification script.
4. Build and smoke-test the immutable backend image.
5. Build the frontend using the final production API/asset origins.
6. Publish versioned assets before consumers reference them.
7. Push and deploy the backend according to the compatibility order.
8. Deploy the frontend through Pages.
9. Verify direct routes, API/meta versions, representative catalogue data, portraits/fallbacks, and Team Planner browser-local persistence.
10. Keep the previous backend image, Pages deployment, and asset version available until the release is proven healthy.

## 10. Other common changes

### Importer-only changes

Run `./scripts/verify.sh`. Do not deploy anything unless you run a new import and intentionally create a new public database; then use the full data-release flow.

### CI workflow or release-script changes

Run shell syntax checks, `git diff --check`, `./scripts/verify.sh`, public-artifact validation, image build, and smoke test. Do not deploy merely because release tooling changed unless production behavior also changed.

```bash
bash -n scripts/*.sh
./scripts/validate-public-artifacts.sh artifacts/public
./scripts/build-production-image.sh
./scripts/smoke-test-image.sh
```

### Dependency updates

Run the complete verification workflow. Frontend dependencies require a Pages release; backend dependencies require a new immutable backend image. Importer development dependencies alone require no deployment unless they produce a new approved database.

### CORS, domain, or DNS changes

Update DNS/TLS first where possible. Update backend allowed origins and deploy the backend image/config. Rebuild the frontend if its API or asset origin changed. Verify exact schemes and hosts; CORS is not authentication.

### Documentation-only changes

Run lightweight checks such as `git diff --check`. No application deployment is required unless documentation is itself published by a separate site.

## 11. Final release record

For every production release, record at least:

- Git commit and working-tree status.
- Exact backend registry image tag/digest.
- Database SHA-256 and import ID.
- Game/data/assets versions.
- Cloudflare Pages deployment/commit.
- Asset manifest/version.
- Date, operator, verification results, and any warnings accepted.
- Previous backend/frontend/asset versions to use for rollback.

Do not store credentials, local extraction paths, or raw proprietary artifacts in the release record.
