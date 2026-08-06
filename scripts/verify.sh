#!/usr/bin/env bash
set -euo pipefail

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repository_root"

PYTHONPATH=src python3 -m unittest discover -s tests -v
dotnet restore api/Cta.Api.Tests/Cta.Api.Tests.csproj
dotnet build api/Cta.Api.Tests/Cta.Api.Tests.csproj --no-restore
dotnet test api/Cta.Api.Tests/Cta.Api.Tests.csproj --no-build --no-restore
npm ci --prefix web/cta-web
npm test --prefix web/cta-web
npm run build --prefix web/cta-web
