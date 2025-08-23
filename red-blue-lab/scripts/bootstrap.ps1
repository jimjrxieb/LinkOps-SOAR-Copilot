# WHIS Red vs Blue Lab - Victim Bootstrap Script
# Installs monitoring tools and intentionally vulnerable configurations

param(
    [Parameter(Mandatory=$true)][string]$SplunkHecUrl,
    [Parameter(Mandatory=$true)][string]$SplunkHecToken,
    [Parameter(Mandatory=$true)][string]$LcSensorKey
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Create setup directory
$SetupDir = "C:\WhisSetup"
New-Item -Path $SetupDir -ItemType Directory -Force | Out-Null
Set-Location $SetupDir

# Start logging
Start-Transcript -Path "$SetupDir\bootstrap.log" -Append

Write-Host "🎯 Starting WHIS Red vs Blue Lab Bootstrap..."
Write-Host "📊 Installing monitoring tools for training data collection"

# URLs for installers
$SysmonUrl = "https://download.sysinternals.com/files/Sysmon.zip"
$SysmonConfigUrl = "https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml"
$SplunkUfUrl = "https://download.splunk.com/products/universalforwarder/releases/9.2.1/windows/splunkforwarder-9.2.1-78803f08aabb-x64.msi"
$LcMsiUrl = "https://downloads.limacharlie.io/sensor/windows/latest"

try {
    # =====================================================
    # 1. INSTALL SYSMON
    # =====================================================
    Write-Host "🔍 Installing Sysmon..."
    
    $wc = New-Object System.Net.WebClient
    $SysmonZip = "$SetupDir\Sysmon.zip"
    $SysmonConfig = "$SetupDir\sysmon.xml"
    
    $wc.DownloadFile($SysmonUrl, $SysmonZip)
    $wc.DownloadFile($SysmonConfigUrl, $SysmonConfig)
    
    Expand-Archive -Path $SysmonZip -DestinationPath "$SetupDir\Sysmon" -Force
    
    $SysmonExe = Get-ChildItem "$SetupDir\Sysmon" -Filter "Sysmon64.exe" -Recurse | Select-Object -First 1
    
    & $SysmonExe.FullName -accepteula -i $SysmonConfig
    Write-Host "✅ Sysmon installed successfully"
    
    # =====================================================
    # 2. INSTALL SPLUNK UNIVERSAL FORWARDER
    # =====================================================
    Write-Host "📊 Installing Splunk Universal Forwarder..."
    
    $SplunkMsi = "$SetupDir\splunk_uf.msi"
    $wc.DownloadFile($SplunkUfUrl, $SplunkMsi)
    
    # Install Splunk UF silently
    Start-Process "msiexec.exe" -ArgumentList "/i `"$SplunkMsi`" AGREETOLICENSE=Yes /qn" -Wait -NoNewWindow
    
    # Configure Splunk UF
    $SplunkEtc = "C:\Program Files\SplunkUniversalForwarder\etc\system\local"
    New-Item -ItemType Directory -Path $SplunkEtc -Force | Out-Null
    
    # Inputs configuration
    @"
[default]
host = VULN-WIN-01

# Windows Event Logs
[WinEventLog://Security]
disabled = 0
index = whis_lab

[WinEventLog://System]
disabled = 0
index = whis_lab

[WinEventLog://Application]
disabled = 0  
index = whis_lab

# PowerShell logs
[WinEventLog://Microsoft-Windows-PowerShell/Operational]
disabled = 0
index = whis_lab

# Sysmon logs
[WinEventLog://Microsoft-Windows-Sysmon/Operational]
disabled = 0
index = whis_lab
"@ | Out-File -FilePath "$SplunkEtc\inputs.conf" -Encoding ASCII
    
    # Outputs configuration
    @"
[httpout]
httpEventCollectorToken = $SplunkHecToken
uri = $SplunkHecUrl

[indexAndForward]
index = false
"@ | Out-File -FilePath "$SplunkEtc\outputs.conf" -Encoding ASCII
    
    # Start Splunk UF service
    & "C:\Program Files\SplunkUniversalForwarder\bin\splunk.exe" start --accept-license --answer-yes
    Write-Host "✅ Splunk Universal Forwarder configured and started"
    
    # =====================================================
    # 3. INSTALL LIMACHARLIE
    # =====================================================
    Write-Host "🛰️ Installing LimaCharlie sensor..."
    
    $LcMsi = "$SetupDir\limacharlie.msi"
    $wc.DownloadFile($LcMsiUrl, $LcMsi)
    
    Start-Process "msiexec.exe" -ArgumentList "/i `"$LcMsi`" /qn SENSOR_KEY=`"$LcSensorKey`"" -Wait -NoNewWindow
    Write-Host "✅ LimaCharlie sensor installed"
    
    # =====================================================
    # 4. CONFIGURE INTENTIONALLY VULNERABLE SETTINGS
    # =====================================================
    Write-Host "🔓 Configuring vulnerable settings for red team training..."
    
    # Enable file sharing with weak permissions
    if ($true) {  # Based on lab scenario
        New-Item -Path "C:\VulnShare" -ItemType Directory -Force | Out-Null
        New-SmbShare -Name "vulnshare" -Path "C:\VulnShare" -FullAccess "Everyone" -Force
        Write-Host "✅ Created vulnerable file share"
    }
    
    # Disable Windows Defender (for training purposes only)
    Set-MpPreference -DisableRealtimeMonitoring $true -Force
    Write-Host "✅ Disabled Windows Defender (training lab only)"
    
    # Configure weak password policy
    secedit /export /cfg "$SetupDir\current.cfg" | Out-Null
    $content = Get-Content "$SetupDir\current.cfg"
    $content = $content -replace "MinimumPasswordLength = \d+", "MinimumPasswordLength = 1"
    $content = $content -replace "PasswordComplexity = 1", "PasswordComplexity = 0"
    $content | Set-Content "$SetupDir\weak.cfg"
    secedit /configure /db secedit.sdb /cfg "$SetupDir\weak.cfg" /quiet
    Write-Host "✅ Applied weak password policy"
    
    # =====================================================
    # 5. CREATE DECOY FILES AND ACCOUNTS
    # =====================================================
    Write-Host "🎭 Creating decoy environment..."
    
    # Create fake sensitive files
    New-Item -Path "C:\Users\$env:USERNAME\Desktop\passwords.txt" -ItemType File -Force | Out-Null
    "admin:password123`r`nroot:admin`r`nservice:changeme" | Out-File "C:\Users\$env:USERNAME\Desktop\passwords.txt"
    
    # Create fake database connection file
    New-Item -Path "C:\VulnShare\database.config" -ItemType File -Force | Out-Null
    "server=prod-db.company.local`r`nuser=sa`r`npassword=StrongPassword2024!" | Out-File "C:\VulnShare\database.config"
    
    Write-Host "✅ Created decoy files for red team discovery"
    
    # =====================================================
    # 6. INSTALL VULNERABLE SOFTWARE
    # =====================================================
    Write-Host "📦 Installing intentionally vulnerable software..."
    
    # Install old version of software for exploitation practice
    # Note: In real deployment, replace with actual vulnerable software packages
    Write-Host "ℹ️ Vulnerable software installation placeholder (customize for specific training scenarios)"
    
    # =====================================================
    # 7. FINAL SETUP AND VALIDATION
    # =====================================================
    Write-Host "🔄 Finalizing setup..."
    
    # Generate initial test events for validation
    Write-EventLog -LogName Application -Source "Application" -EventId 1000 -Message "WHIS Lab initialized - monitoring active"
    
    # Test PowerShell logging
    powershell -Command "Write-Host 'Testing PowerShell monitoring - WHIS Lab'"
    
    Write-Host "🎉 WHIS Red vs Blue Lab bootstrap completed successfully!"
    Write-Host ""
    Write-Host "📋 SETUP SUMMARY:"
    Write-Host "✅ Sysmon: Installed with SwiftOnSecurity config"
    Write-Host "✅ Splunk UF: Forwarding to HEC endpoint"
    Write-Host "✅ LimaCharlie: EDR sensor active"
    Write-Host "✅ Vulnerable configs: Applied for training"
    Write-Host "✅ Decoy files: Created for red team practice"
    Write-Host ""
    Write-Host "⚠️  SECURITY NOTICE: This system is INTENTIONALLY VULNERABLE"
    Write-Host "🎯 Purpose: Red vs Blue team training only"
    Write-Host "🔒 Ensure proper network isolation from production"
    
}
catch {
    Write-Host "❌ Bootstrap failed: $($_.Exception.Message)"
    throw
}
finally {
    Stop-Transcript
}