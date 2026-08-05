param(
  [string[]]$Source,
  [Parameter(Mandatory=$true)][string]$OutputDir,
  [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$keywords = @("Google", "Play Games", "Android", "Emulator", "Crosvm", "godzilab", "godzillab", "imperia", "stillfront", "crush", "idlerpg", "com.godzilab.idlerpg")
$extensions = @(".apk",".apks",".xapk",".zip",".obb",".db",".sqlite",".sqlite3",".json",".xml",".csv",".tsv",".bytes",".bin",".dat",".bundle",".asset",".assets",".resource",".resources",".resS",".manifest",".catalog",".hash",".pack",".pak",".ucas",".utoc",".proto",".pb",".dll",".so",".dex",".img",".png",".jpg",".jpeg",".ico")

if (-not $Source -or $Source.Count -eq 0) {
  $Source = @(
    "$env:LOCALAPPDATA\Google\Play Games",
    "$env:PROGRAMDATA\Google\Play Games",
    "$env:PROGRAMDATA\Google\Play Games Services",
    "$env:ProgramFiles\Google\Play Games",
    "$env:ProgramFiles\Google\Play Games Services"
  )
}

if ($DryRun) {
  "Would scan:" | Write-Output
  $Source | ForEach-Object { "  $_" | Write-Output }
  return
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$outFile = Join-Path $OutputDir "candidate-paths.txt"
$logFile = Join-Path $OutputDir "find-game-files.log"
Set-Content -Path $outFile -Value "" -Encoding utf8
Set-Content -Path $logFile -Value "" -Encoding utf8

foreach ($root in $Source) {
  if (-not (Test-Path -LiteralPath $root)) {
    Add-Content -Path $logFile -Value "missing source: $root"
    continue
  }
  try {
    Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction SilentlyContinue |
      Where-Object {
        $ext = $_.Extension.ToLowerInvariant()
        $path = $_.FullName.ToLowerInvariant()
        ($extensions -contains $ext) -or ($keywords | Where-Object { $path.Contains($_.ToLowerInvariant()) })
      } |
      Sort-Object FullName -Unique |
      ForEach-Object { Add-Content -Path $outFile -Value $_.FullName -Encoding utf8 }
  } catch {
    Add-Content -Path $logFile -Value "error scanning ${root}: $($_.Exception.Message)"
  }
}

Write-Output "Wrote $outFile"
Write-Output "Wrote $logFile"
