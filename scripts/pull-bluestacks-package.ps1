param(
  [string]$Package = "com.godzilab.idlerpg",
  [string]$Serial = "127.0.0.1:5555",
  [string]$OutputDir = (Join-Path $env:TEMP "cta-game-extraction")
)

$ErrorActionPreference = "Stop"

$candidates = @(
  "$env:ProgramFiles\BlueStacks_nxt\HD-Adb.exe",
  "${env:ProgramFiles(x86)}\BlueStacks_nxt\HD-Adb.exe",
  "$env:ProgramFiles\BlueStacks\HD-Adb.exe",
  "${env:ProgramFiles(x86)}\BlueStacks\HD-Adb.exe"
)
$adb = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $adb) {
  throw "BlueStacks HD-Adb.exe was not found."
}

$apkDir = Join-Path $OutputDir "apk"
$sharedDir = Join-Path $OutputDir "shared-data"
$logDir = Join-Path $OutputDir "logs"
New-Item -ItemType Directory -Force -Path $apkDir, $sharedDir, $logDir | Out-Null

Write-Output "OUTPUT_DIR=$OutputDir"
Write-Output "SERIAL=$Serial"

$packagePaths = @(
  & $adb -s $Serial shell pm path $Package |
    Where-Object { $_ -like "package:*" } |
    ForEach-Object { $_.Substring("package:".Length).Trim() }
)

if ($packagePaths.Count -eq 0) {
  throw "Package $Package was not found on $Serial."
}

$packagePaths | Set-Content -Path (Join-Path $logDir "$Package.pm-path.txt") -Encoding utf8
& $adb -s $Serial shell dumpsys package $Package |
  Set-Content -Path (Join-Path $logDir "$Package.dumpsys-package.txt") -Encoding utf8

Write-Output "=== PULLING APKS ==="
foreach ($remotePath in $packagePaths) {
  Write-Output $remotePath
  & $adb -s $Serial pull $remotePath $apkDir
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to pull $remotePath"
  }
}

Write-Output "=== INVENTORYING SHARED DATA ==="
& $adb -s $Serial shell find "/sdcard/Android/data/$Package" -type f -print |
  Set-Content -Path (Join-Path $logDir "$Package.shared-files.txt") -Encoding utf8

Write-Output "=== PULLING SHARED DATA ==="
& $adb -s $Serial pull "/sdcard/Android/data/$Package/." $sharedDir
if ($LASTEXITCODE -ne 0) {
  Write-Warning "Shared-data pull was incomplete; APK retrieval can still be analyzed."
}

Write-Output "=== SHA256 ==="
$sha256 = [System.Security.Cryptography.SHA256]::Create()
$hashes = Get-ChildItem -Path $apkDir -File | ForEach-Object {
  $stream = [System.IO.File]::OpenRead($_.FullName)
  try {
    $hash = [System.BitConverter]::ToString($sha256.ComputeHash($stream)).Replace("-", "")
    [PSCustomObject]@{ Hash = $hash; Path = $_.FullName }
  } finally {
    $stream.Dispose()
  }
}
$sha256.Dispose()
$hashes | Format-Table -AutoSize
$hashes | ConvertTo-Csv -NoTypeInformation |
  Set-Content -Path (Join-Path $logDir "$Package.apk-sha256.csv") -Encoding utf8

Write-Output "DONE=$OutputDir"
