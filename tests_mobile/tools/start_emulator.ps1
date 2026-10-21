<#
.SYNOPSIS
  Mobil run oldidan: Android emulyator + Appium + ilovani bitta buyruq bilan tayyorlaydi.

.DESCRIPTION
  powershell -File tests_mobile/tools/start_emulator.ps1            # headless (-no-window), tavsiya
  powershell -File tests_mobile/tools/start_emulator.ps1 -Window    # oynali rejim (ixtiyoriy)

  1. Emulyator allaqachon `device` va sys.boot_completed=1 bo'lsa - qayta yoqilmaydi.
  2. Aks holda: SDK ichidagi qotgan emulator/qemu/crashpad jarayonlari o'chiriladi
     (QMEmulatorService'ga TEGILMAYDI), AVD *.lock fayllari tozalanadi va emulyator
     ANDROID_SDK_ROOT/ANDROID_HOME = %LOCALAPPDATA%\Android\Sdk bilan yashirin ishga tushadi
     (tizim ANDROID_HOME WinGet platform-tools'ga qaraydi - "Broken AVD system path").
     2026-10-20: oynali va oddiy swiftshader rejimi GPU DisplaySurfaceGlContextHelper xatosi
     bilan qulab, ko'rinmas crash dialogni kutib qotgan; faqat -no-window ishlagan.
  3. sys.boot_completed=1 kutiladi (timeout'da log oxiri chiqadi).
  4. Appium 4723 tinglanmasa - alohida konsol oynada ochiladi (sarlavha "Appium - YOPMANG").
  5. Ilova bir marta oldindan ochiladi (sovuq start splash timeout bermasin).
  6. Yakuniy holat chiqadi; hammasi joyida bo'lsa exit 0, aks holda 1.
#>
param(
    [switch]$Window,
    [string]$Avd = "Medium_Phone_API_37.0",
    [int]$BootTimeoutSec = 300,
    [int]$AppiumPort = 4723,
    [string]$AppPackage = "uz.greenwhite.smartup24"
)

# "Stop" EMAS: PS 5.1 da native buyruq stderr (2>$null) Stop rejimida xato deb ko'tariladi
$ErrorActionPreference = "Continue"
$Sdk = Join-Path $env:LOCALAPPDATA "Android\Sdk"
$EmulatorExe = Join-Path $Sdk "emulator\emulator.exe"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$LogDir = Join-Path $RepoRoot "test-results"
$Log = Join-Path $LogDir "emulator.log"
$ErrLog = Join-Path $LogDir "emulator.err.log"

# adb: PATH dagisi (Appium/testlar ishlatadigan server bilan bir xil), bo'lmasa SDK'niki
$AdbCmd = Get-Command adb -ErrorAction SilentlyContinue
$Adb = if ($AdbCmd) { $AdbCmd.Source } else { Join-Path $Sdk "platform-tools\adb.exe" }

function Write-Step([string]$msg) { Write-Host "[emulator] $msg" -ForegroundColor Cyan }

function Get-EmulatorSerial {
    # "emulator-5554<TAB>device" (offline/unauthorized emas)
    $lines = & $Adb devices 2>$null
    foreach ($l in $lines) {
        if ($l -match '^(emulator-\d+)\s+device\s*$') { return $Matches[1] }
    }
    return $null
}

function Test-Booted([string]$serial) {
    if (-not $serial) { return $false }
    $v = (& $Adb -s $serial shell getprop sys.boot_completed 2>$null | Out-String).Trim()
    return $v -eq "1"
}

function Test-Port([int]$port) {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        $ar = $c.BeginConnect("127.0.0.1", $port, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(1000)) { return $false }
        $c.EndConnect($ar)
        return $true
    } catch {
        return $false
    } finally {
        $c.Close()
    }
}

function Show-LogTail {
    foreach ($f in @($Log, $ErrLog)) {
        if (Test-Path $f) {
            Write-Host "----- $f (oxirgi 40 qator) -----" -ForegroundColor Yellow
            Get-Content $f -Tail 40
        }
    }
}

function Stop-StuckEmulator {
    # Faqat SDK ichidagi jarayonlar: emulator*, qemu-system*, crashpad_handler.
    # QMEmulatorService (va boshqa ilovalarning crashpad'i) tegilmaydi.
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -match '^(emulator.*|qemu-system.*|crashpad_handler)$' -and
        $_.Name -ne 'QMEmulatorService' -and
        $_.Path -and $_.Path.StartsWith($Sdk, [System.StringComparison]::OrdinalIgnoreCase)
    }
    foreach ($p in $procs) {
        Write-Step "o'chirilmoqda: $($p.Name) (pid $($p.Id))"
        try { Stop-Process -Id $p.Id -Force -ErrorAction Stop } catch { Write-Step "  o'chmadi: $($_.Exception.Message)" }
    }
    if ($procs) { Start-Sleep -Seconds 3 }   # fayl qulflari bo'shasin
}

function Clear-AvdLocks {
    $ini = Join-Path $env:USERPROFILE ".android\avd\$Avd.ini"
    $avdPath = Join-Path $env:USERPROFILE ".android\avd\$Avd.avd"
    if (Test-Path $ini) {
        $line = Get-Content $ini | Where-Object { $_ -like "path=*" } | Select-Object -First 1
        if ($line) { $avdPath = $line.Substring(5) }
    }
    if (-not (Test-Path $avdPath)) { throw "AVD papkasi topilmadi: $avdPath (AVD nomi: $Avd)" }
    Get-ChildItem -Path $avdPath -Filter "*.lock" -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Step "lock o'chirilmoqda: $($_.FullName)"
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Start-Emulator {
    if (-not (Test-Path $EmulatorExe)) { throw "emulator.exe topilmadi: $EmulatorExe" }
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $emuArgs = @("-avd", $Avd, "-no-snapshot-load", "-gpu", "swiftshader_indirect", "-no-boot-anim")
    if (-not $Window) { $emuArgs += "-no-window" }
    # Faqat shu jarayon (va bolalari) uchun - tizim o'zgaruvchilari o'zgarmaydi
    $oldHome, $oldRoot = $env:ANDROID_HOME, $env:ANDROID_SDK_ROOT
    $env:ANDROID_HOME = $Sdk
    $env:ANDROID_SDK_ROOT = $Sdk
    try {
        $style = if ($Window) { "Normal" } else { "Hidden" }
        Write-Step "ishga tushirilmoqda: emulator $($emuArgs -join ' ')  (log: $Log)"
        $proc = Start-Process -FilePath $EmulatorExe -ArgumentList $emuArgs -WindowStyle $style `
            -RedirectStandardOutput $Log -RedirectStandardError $ErrLog -PassThru
    } finally {
        $env:ANDROID_HOME, $env:ANDROID_SDK_ROOT = $oldHome, $oldRoot
    }
    return $proc
}

function Wait-Boot($proc) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $BootTimeoutSec) {
        if ($proc -and $proc.HasExited) {
            Write-Host "Emulyator jarayoni tugab qoldi (exit $($proc.ExitCode))." -ForegroundColor Red
            Show-LogTail
            return $null
        }
        $serial = Get-EmulatorSerial
        if (Test-Booted $serial) {
            Write-Step "boot tugadi: $serial ($([int]$sw.Elapsed.TotalSeconds) s)"
            return $serial
        }
        Start-Sleep -Seconds 5
    }
    Write-Host "Timeout: $BootTimeoutSec s ichida sys.boot_completed=1 bo'lmadi." -ForegroundColor Red
    Show-LogTail
    return $null
}

function Ensure-Appium {
    if (Test-Port $AppiumPort) { Write-Step "Appium $AppiumPort allaqachon tinglayapti"; return $true }
    $title = "Appium " + [char]0x2014 + " YOPMANG"
    $cmd = "`$Host.UI.RawUI.WindowTitle = '$title'; appium --port $AppiumPort --use-plugins=inspector --allow-cors"
    Write-Step "Appium alohida oynada ochilmoqda (sarlavha: $title)"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-NoProfile", "-Command", $cmd) | Out-Null
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt 60) {
        if (Test-Port $AppiumPort) { Write-Step "Appium $AppiumPort tayyor"; return $true }
        Start-Sleep -Seconds 2
    }
    Write-Host "Appium 60 s ichida $AppiumPort portini ochmadi - 'Appium' oynasini tekshiring." -ForegroundColor Red
    return $false
}

function Test-AppInstalled([string]$serial) {
    if (-not $serial) { return $false }
    $out = (& $Adb -s $serial shell pm list packages $AppPackage 2>$null | Out-String)
    return $out -match "package:$([regex]::Escape($AppPackage))\s"
}

# -- 1. allaqachon tayyormi ----------------------------------------------------------
$serial = Get-EmulatorSerial
if (Test-Booted $serial) {
    Write-Step "emulyator allaqachon ishlayapti: $serial (boot=1) - qayta yoqilmaydi"
} else {
    # -- 2. tozalash va ishga tushirish ----------------------------------------------
    if ($serial) { Write-Step "$serial bor, lekin boot tugamagan/qotgan - qayta yoqiladi" }
    Stop-StuckEmulator
    Clear-AvdLocks
    $proc = Start-Emulator
    # -- 3. boot kutish --------------------------------------------------------------
    $serial = Wait-Boot $proc
}

# -- 4. Appium ----------------------------------------------------------------------
$appiumOk = Ensure-Appium

# -- 5. ilovani oldindan ochish ------------------------------------------------------
$installed = Test-AppInstalled $serial
if ($serial -and $installed) {
    Write-Step "ilova oldindan ochilmoqda: $AppPackage"
    & $Adb -s $serial shell monkey -p $AppPackage -c android.intent.category.LAUNCHER 1 2>&1 | Out-Null
}

# -- 6. holat ------------------------------------------------------------------------
$booted = Test-Booted $serial
Write-Host ""
Write-Host "================ HOLAT ================"
Write-Host ("Device       : " + $(if ($serial) { $serial } else { "YO'Q" }))
Write-Host ("Boot         : " + $(if ($booted) { "1 (tayyor)" } else { "tayyor EMAS" }))
Write-Host ("Appium $AppiumPort : " + $(if ($appiumOk) { "tinglayapti" } else { "YO'Q" }))
Write-Host ("Ilova        : " + $(if ($installed) { "$AppPackage o'rnatilgan" } else { "$AppPackage O'RNATILMAGAN (INSTALL_APP=1 bilan run yoki qo'lda o'rnating)" }))
Write-Host "======================================="
if ($serial -and $booted -and $appiumOk -and $installed) { exit 0 } else { exit 1 }
