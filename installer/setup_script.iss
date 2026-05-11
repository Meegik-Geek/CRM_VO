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
; Ліцензія тепер тут
LicenseFile=installer\license_uk.txt 

[Languages]
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Types]
Name: "full"; Description: "Повна інсталяція"
Name: "custom"; Description: "Вибіркова інсталяція"; Flags: iscustom

[Components]
Name: "app"; Description: "Програма CRM Вступ.Офіс"; Types: full custom; Flags: fixed
Name: "postgres"; Description: "Сервер бази даних PostgreSQL"; Types: full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "build\exe.win-amd64-3.14\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: app
Source: "postgresql-installer.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall; Components: postgres

[Icons]
Name: "{group}\CRM Вступ.Офіс"; Filename: "{app}\main.exe"; Components: app
Name: "{group}\Налаштування системи"; Filename: "{app}\installer.exe"; Components: app
Name: "{autodesktop}\CRM Вступ.Офіс"; Filename: "{app}\main.exe"; Tasks: desktopicon; Components: app

[Run]
; 1. Встановлення PostgreSQL (якщо вибрано компонент) - запускається ТИХО під час інсталяції
Filename: "{tmp}\postgresql-installer.exe"; Parameters: "--mode unattended --unattendedmodeui none --postgrespassword postgres"; StatusMsg: "Встановлення PostgreSQL (це може зайняти 1-2 хвилини)..."; Components: postgres; Flags: runhidden

; 2. АВТОМАТИЧНИЙ запуск Майстра налаштування БД (одразу після копіювання файлів)
Filename: "{app}\installer.exe"; StatusMsg: "Запуск майстра налаштування бази даних..."; Flags: nowait

; 3. Запуск самої програми - ВИДАЛЕНО, щоб користувач спочатку налаштував базу через майстер
; Користувач запустить її сам через ярлик після налаштування.



