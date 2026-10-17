# register-task.ps1 - register the usbipd auto-attach scheduled task (run elevated)
$ErrorActionPreference = 'Stop'

$taskName = 'usbipd-auto-attach'
$scriptPath = 'C:\Users\Garin\usbipd-auto-attach\auto-attach-usbipd.ps1'

if (-not (Test-Path $scriptPath)) {
    Write-Error "Script not found: $scriptPath"
    exit 1
}

# require admin
$id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$p = New-Object System.Security.Principal.WindowsPrincipal($id)
if (-not $p.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error 'Please run this from an elevated (Administrator) PowerShell.'
    exit 1
}

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $scriptPath + '"')
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$trigger.Delay = 'PT30S'
$principal = New-ScheduledTaskPrincipal -UserId ("$env:USERDOMAIN\" + $env:USERNAME) -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Auto-attach ESP32-S3 to WSL at logon' -Force | Out-Null

Write-Host ('Task "' + $taskName + '" registered OK.')
