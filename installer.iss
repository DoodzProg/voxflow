; installer.iss
; Inno Setup 6 script for AcouZ v1.0.2
;
; Prerequisites:
;   1. Run `pyinstaller acouz.spec` — produces dist\AcouZ\
;   2. Install Inno Setup 6: https://jrsoftware.org/isinfo.php
;   3. Compile:  iscc installer.iss
;   4. Output:   dist\AcouZSetup.exe

#define AppName      "AcouZ"
#define AppVersion   "1.0.2"
#define AppPublisher "DoodzProg"
#define AppURL       "https://github.com/DoodzProg/acouz"
#define AppExeName   "AcouZ.exe"
#define SourceDir    "dist\AcouZ"

[Setup]
; --- Identity ---
AppId={{A3F2C1B0-9E4D-4A7F-8B6C-2D5E0F3A1C8B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; --- Installation target ---
; No admin rights required: installs per-user under %LocalAppData%
DefaultDirName={localappdata}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

; --- Output ---
OutputDir=dist
OutputBaseFilename=AcouZSetup
SetupIconFile=assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; --- Appearance ---
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}

; --- Misc ---
ChangesEnvironment=no
; Allow re-installing over existing version without asking to uninstall first.
CloseApplications=yes
CloseApplicationsFilter=*.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copy the entire PyInstaller one-folder bundle.
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#AppName}";       Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall AcouZ";  Filename: "{uninstallexe}"
; Desktop shortcut (optional task)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch the app immediately after installation.
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove the startup registry entry on uninstall (if the user had it enabled).
Filename: "reg"; Parameters: "delete ""HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"" /v ""{#AppName}"" /f"; Flags: runhidden; StatusMsg: "Removing startup entry..."

[Code]
// ---------------------------------------------------------------------------
// Update the startup registry entry path if the user previously enabled
// "Launch at Windows startup" — the install path may have changed.
// ---------------------------------------------------------------------------
procedure UpdateStartupPath();
var
  RegKey, OldPath, NewPath: String;
begin
  RegKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Run';
  NewPath := ExpandConstant('"{app}\{#AppExeName}"');

  // Only update if an AcouZ entry already exists (user had it enabled).
  if RegQueryStringValue(HKCU, RegKey, '{#AppName}', OldPath) then
  begin
    RegWriteStringValue(HKCU, RegKey, '{#AppName}', NewPath);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    UpdateStartupPath();
end;
