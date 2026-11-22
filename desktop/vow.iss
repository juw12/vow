; Vow for Windows - per-user installer (no admin rights). build.py compiles it with:
;   iscc /DAppVersion=1.0.0 /DSourceDir=<dist\Vow> /DOutputDir=<dist> /DIconFile=<build\vow.ico> vow.iss
; Installs to %LOCALAPPDATA%\Programs\Vow, adds Vow to the Start menu (and optionally the desktop) and lists it
; in Settings > Apps. The window keeps its data (what you saved in it) in %LOCALAPPDATA%\Vow, which
; uninstalling leaves in place so a reinstall finds it again.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "dist\Vow"
#endif
#ifndef OutputDir
  #define OutputDir "dist"
#endif
#ifndef IconFile
  #define IconFile "build\vow.ico"
#endif

[Setup]
AppId={{E81247BA-698B-569E-A6DE-E1E1C366EEFB}
AppName=Vow
AppVersion={#AppVersion}
AppVerName=Vow {#AppVersion}
AppPublisher=Juwen Lie
AppPublisherURL=https://juw12.github.io/vow/
AppSupportURL=https://github.com/juw12/vow
DefaultDirName={autopf}\Vow
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=Vow-Windows-Setup
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\Vow.exe
UninstallDisplayName=Vow
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=no
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Vow"; Filename: "{app}\Vow.exe"; Comment: "Free, private commitment contracts with a stake and a witness"
Name: "{userdesktop}\Vow"; Filename: "{app}\Vow.exe"; Comment: "Free, private commitment contracts with a stake and a witness"; Tasks: desktopicon

[Run]
Filename: "{app}\Vow.exe"; Description: "{cm:LaunchProgram,Vow}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\Vow.exe"; Parameters: "--stop"; Flags: runhidden waituntilterminated; RunOnceId: "StopVow"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  { Updating: close an open Vow window first so its files can be replaced. }
  if FileExists(ExpandConstant('{app}\Vow.exe')) then
    Exec(ExpandConstant('{app}\Vow.exe'), '--stop', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
