; Inno Setup Script for Burgood Access Control
; Ushbu fayl Inno Setup orqali BurgoodAccessControl_Setup.exe yaratish uchun xizmat qiladi

#define MyAppName "Burgood Access Control"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Burgood Systems"
#define MyAppURL "https://burgood.uz"
#define MyAppExeName "BurgoodAccessControl.exe"

[Setup]
AppId={{E5813734-7D68-45F4-A746-817D50DE29BC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=BurgoodAccessControl_Setup
SetupIconFile=..\frontend\public\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Asosiy dastur fayllari (PyInstaller orqali yig'ilgan to'liq papka)
Source: "..\dist\BurgoodAccessControl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Frontend dist
Source: "..\frontend\dist\*"; DestDir: "{app}\frontend\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
; Backend manba kodlari va ma'lumotlar bazasi
Source: "..\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\frontend\public\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\frontend\public\app_icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
