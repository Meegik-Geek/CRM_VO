; Скрипт Inno Setup для CRM "Вступ.Офіс"

[Setup]
AppName=CRM Вступ.Офіс
AppVersion=1.0.4
DefaultDirName={autopf}\CRM_Vstup_Office
DefaultGroupName=CRM Вступ.Офіс
UninstallDisplayIcon={app}\main.exe
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:Inno Setup Output
OutputBaseFilename=Setup_Vstup2026_Full
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
SourceDir=..
SetupIconFile=resource\logo.ico
LicenseFile=installer\license_uk.txt 

[Languages]
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "installpostgres"; Description: "Встановити сервер бази даних PostgreSQL (обов'язково для сервера)"; GroupDescription: "Додаткові компоненти:"; Flags: checkedonce

[Files]
Source: "build\exe.win-amd64-3.14\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "postgresql-installer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CRM Вступ.Офіс"; Filename: "{app}\main.exe"
Name: "{group}\Налаштування системи"; Filename: "{app}\installer.exe"
Name: "{autodesktop}\CRM Вступ.Офіс"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Run]
; 1. Запуск звичайного встановлення PostgreSQL (з вікнами та налаштуваннями)
Filename: "{app}\postgresql-installer.exe"; Description: "Встановлення PostgreSQL"; StatusMsg: "Очікування завершення встановлення PostgreSQL..."; Tasks: installpostgres; Flags: waituntilterminated

; 2. АВТОМАТИЧНИЙ запуск Майстра налаштування БД (після завершення інсталяції PostgreSQL)
Filename: "{app}\installer.exe"; StatusMsg: "Запуск майстра налаштування бази даних..."; Flags: nowait
