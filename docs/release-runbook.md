# Unified release runbook

Every frontend, backend, database, or asset change produces one immutable image. See [deployment.md](deployment.md) for details.

```bash
git status --short
git diff --check
git check-ignore local-release/ local/proprietary/
git diff --cached --name-only

export CTA_ASSETS_VERSION=YYYY-MM-DD
export VCS_REF="$(git rev-parse --short=7 HEAD)"
export FLY_APP_NAME=<app>
export RELEASE_IMAGE="registry.fly.io/${FLY_APP_NAME}:${CTA_ASSETS_VERSION}-${VCS_REF}"

./scripts/prepare-release.sh
# Review local-release/data and local-release/assets now.
./scripts/release-local.sh
./scripts/inspect-production-image.sh "$RELEASE_IMAGE"
```

`release-local.sh` verifies, builds, starts, and smoke-tests the exact image. It does not push or deploy. Never reuse a tag, build production in GitHub, or stage `local-release/`, generated SQLite, extraction data, or proprietary assets.

After local approval only:

```bash
flyctl auth docker
docker push "$RELEASE_IMAGE"
FLY_IMAGE_REF="$RELEASE_IMAGE" ./scripts/deploy-fly-image.sh
FLY_IMAGE_REF="$RELEASE_IMAGE" ./scripts/deploy-fly-image.sh --execute
```

Verify `https://<app>.fly.dev/`, direct SPA routes, health/readiness, metadata, hero API, portraits, and UI icons. Roll back with the same deploy script using a prior immutable tag or digest.
