# Phase 1: Identifiers

## Confirmed

- Game display name: `Crush Them All - PVP Idle RPG`
- Android package name: `com.godzilab.idlerpg`
- Google Play Games user data: `C:\Users\<windows-user>\AppData\Local\Google\Play Games`
- Google Play Games program data: `C:\ProgramData\Google\Play Games`
- Google Play Games Services program data: `C:\ProgramData\Google\Play Games Services`
- Google Play Games install: `C:\Program Files\Google\Play Games`
- Google Play Games Services install: `C:\Program Files\Google\Play Games Services`
- Emulator executable found: `C:\Program Files\Google\Play Games\current\emulator\crosvm.exe`
- Client executable found: `C:\Program Files\Google\Play Games\current\client\client.exe`
- Service executable found: `C:\Program Files\Google\Play Games\current\service\Service.exe`

## Evidence

Commands run:

```bash
find /mnt/c/ProgramData/Google -maxdepth 5 -type f -o -type d
find /mnt/c/'Program Files'/Google/'Play Games' -maxdepth 4 -type f -o -type d
find /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games' -maxdepth 4 -type f -o -type d
rg -a -i --glob '!CEF/**' 'Crush Them All|crushthemall|Imperia|Stillfront|Godzillab|Godzilab|com\.[A-Za-z0-9_.-]+'
```

Key log evidence from `C:\Users\<windows-user>\AppData\Local\Google\Play Games\Logs\Client.log`:

- `install_game_request { package_name: "com.godzilab.idlerpg" ... }`
- `create_shortcuts_request { package_name: "com.godzilab.idlerpg" title: "Crush Them All - PVP Idle RPG" ... }`
- `installed_version_info { version_code: 200822 }`
- `launch_game_request { package_name: "com.godzilab.idlerpg" ... }`
- lifecycle transitions: `PENDING`, `DOWNLOADING`, `INSTALLING`, `INSTALLED`, `LAUNCHING`, `RUNNING`, `STOPPING`

Key log evidence from `Logs\emulator_logs\gpu_syslog.log`:

- window title set to `Crush Them All - PVP Idle RPG - <windows-user>`
- icon loaded from `com.godzilab.idlerpg.appicon.ico`

## Relevant Data Roots

- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\store.db`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\image_cache\com.godzilab.idlerpg.*`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img`
- `C:\Program Files\Google\Play Games\current\emulator\avd\aggregate.img`

## Unresolved

- Live Windows process list, loaded modules, and open file handles could not be collected from this WSL session because `powershell.exe` was unavailable.
- The game APK or split APK path was not found as a normal accessible host file during bounded scanning.
- The user AVD image files under `userdata_<instance>.gz5\avd` were metadata-visible but read-restricted from this WSL session.
