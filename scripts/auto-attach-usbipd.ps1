# auto-attach-usbipd.ps1
# Attach ESP32-S3 (VID 303a) to WSL2 automatically at logon.
# Triggered by Windows Task Scheduler with highest privileges (no UAC popup).

$ErrorActionPreference = 'Continue'
$log = Join-Path $env:TEMP 'usbipd-auto-attach.log'

function Log($m) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Out-File -FilePath $log -Append -Encoding utf8
}

Log "===== auto-attach start ====="

# 0) locate usbipd.exe
$usbipd = $null
$cmd = Get-Command usbipd -ErrorAction SilentlyContinue
if ($cmd) { $usbipd = $cmd.Source }
if (-not $usbipd -and (Test-Path "$env:ProgramFiles\usbipd-win\usbipd.exe")) {
    $usbipd = "$env:ProgramFiles\usbipd-win\usbipd.exe"
}
if (-not $usbipd) { Log "usbipd.exe not found, abort"; exit 1 }
Log "usbipd = $usbipd"

# 1) wake up WSL and load vhci-hcd (USB/IP client module; systemd skips it in WSL)
try {
    wsl.exe -e sh -c "true" 2>$null
    wsl.exe -u root sh -c "modprobe vhci-hcd 2>/dev/null || true" 2>$null
} catch {}
Start-Sleep -Seconds 3

# 2) find busid for VID 303a and its current state
$busid = $null
$attached = $false
foreach ($line in (& $usbipd list)) {
    if ($line -match '^\s*([0-9]+-[0-9.]+)\s+303a:') {
        $busid = $Matches[1]
        if ($line -match 'Attached') { $attached = $true }
    }
}
if (-not $busid) {
    Log "no device with VID 303a found, skip (unplugged?)"
    exit 0
}
if ($attached) {
    Log "busid $busid already attached, skip"
    exit 0
}

# 3) ensure bound (binding persists across reboot; this is a safety net)
& $usbipd bind --busid $busid 2>$null | Out-Null

# 4) attach with retry
$ok = $false
for ($i = 1; $i -le 5; $i++) {
    $out = & $usbipd attach --wsl --busid $busid 2>&1
    $code = $LASTEXITCODE
    Log "try ${i}: attach --wsl --busid $busid => exit=$code $($out -join ' ')"
    if ($code -eq 0) { $ok = $true; break }
    Start-Sleep -Seconds 5
}

if ($ok) {
    Log "SUCCESS: $busid attached to WSL"
    exit 0
} else {
    Log "FAILED: could not attach $busid"
    exit 1
}
