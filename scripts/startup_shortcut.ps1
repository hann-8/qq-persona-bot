param(
    [Parameter(Mandatory=$true)][string]$LinkPath,
    [Parameter(Mandatory=$true)][string]$TargetPath,
    [Parameter(Mandatory=$true)][string]$LinkArguments,
    [Parameter(Mandatory=$true)][string]$WorkingDirectory
)
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($LinkPath)
$link.TargetPath = $TargetPath
$link.Arguments = $LinkArguments
$link.WorkingDirectory = $WorkingDirectory
$link.Description = 'QQbot managed current-user startup'
$link.WindowStyle = 7
$link.Save()
