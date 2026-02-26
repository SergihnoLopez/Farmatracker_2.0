
[Setup]
AppName=FarmaTrack
AppVersion=1.0
DefaultDirName={pf}\FarmaTrack
DefaultGroupName=FarmaTrack
OutputDir=.
OutputBaseFilename=FarmaTrack_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\FarmaTrack.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_files\farma_pro_stocker.db"; DestDir: "{app}\default_db"; Flags: ignoreversion

[Icons]
Name: "{group}\FarmaTrack"; Filename: "{app}\FarmaTrack.exe"
Name: "{commondesktop}\FarmaTrack"; Filename: "{app}\FarmaTrack.exe"

[Run]
Filename: "{app}\FarmaTrack.exe"; Description: "Ejecutar FarmaTrack"; Flags: nowait postinstall skipifsilent
