param(
  [string]$Package = "com.godzilab.idlerpg",
  [string]$Serial
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
  $adb = Get-ChildItem -Path $env:ProgramData -Filter HD-Adb.exe -File -Recurse -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
}

if (-not $adb) {
  throw "BlueStacks HD-Adb.exe was not found in the standard install locations or under ProgramData."
}

Write-Output "HD_ADB=$adb"
Write-Output "=== VERSION ==="
& $adb version

Write-Output "=== DEVICES ==="
& $adb start-server
$deviceOutput = & $adb devices -l
$deviceOutput

if (-not $Serial) {
  $connectedSerials = @(
    $deviceOutput |
      Where-Object { $_ -match '^([^\s]+)\s+device(?:\s|$)' } |
      ForEach-Object { $Matches[1] }
  )
  $Serial = $connectedSerials |
    Sort-Object @{ Expression = { if ($_ -eq '127.0.0.1:5555') { 0 } else { 1 } } } |
    Select-Object -First 1
}

if (-not $Serial) {
  throw "No online BlueStacks Android device was found."
}

Write-Output "SELECTED_SERIAL=$Serial"

Write-Output "=== ANDROID IDENTITY ==="
& $adb -s $Serial shell getprop ro.product.manufacturer
& $adb -s $Serial shell getprop ro.product.model
& $adb -s $Serial shell getprop ro.build.version.release
& $adb -s $Serial shell getprop ro.product.cpu.abilist

Write-Output "=== PACKAGE PATHS: $Package ==="
& $adb -s $Serial shell pm path $Package

Write-Output "=== PACKAGE SUMMARY: $Package ==="
& $adb -s $Serial shell dumpsys package $Package |
  Select-String -Pattern "versionCode=|versionName=|codePath=|resourcePath=|primaryCpuAbi=|secondaryCpuAbi=|userId="

Write-Output "=== SHARED DATA ==="
& $adb -s $Serial shell ls -la "/sdcard/Android/data/$Package"
& $adb -s $Serial shell ls -la "/sdcard/Android/obb/$Package"
