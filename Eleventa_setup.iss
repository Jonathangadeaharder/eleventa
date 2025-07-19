; Eleventa_setup.iss
; Inno Setup Script for the Eleventa Application

[Setup]
; NOTE: The AppId is a unique identifier for your application.
; It's recommended to generate a new GUID for each application.
AppId={{F07A4D43-B07B-4E6F-8A5A-6B0C8D6E1F3A}}
AppName=Eleventa
AppVersion=1.0.0
AppPublisher=Your Company Name
DefaultDirName={autopf}\Eleventa
DefaultGroupName=Eleventa
DisableProgramGroupPage=yes
; The output installer will be created in a sub-directory named "installer".
OutputDir=installer
OutputBaseFilename=Eleventa_Setup_v1.0.0
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
; Create the application's data directory in the user's local app data folder.
; This directory will be writable by the application at runtime.
Name: "{localappdata}\Eleventa"; Permissions: users-modify

[Files]
; Copy all files and subdirectories from the PyInstaller output directory.
; The path should be relative to this script file.
Source: "dist\Eleventa\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Eleventa"; Filename: "{app}\Eleventa.exe"
Name: "{group}\{cm:UninstallProgram,Eleventa}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Eleventa"; Filename: "{app}\Eleventa.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Eleventa.exe"; Description: "{cm:LaunchProgram,Eleventa}"; Flags: nowait postinstall skipifsilent