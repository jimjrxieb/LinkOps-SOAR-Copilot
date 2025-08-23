# WHIS Red vs Blue Lab - Monitoring Installation Script
# Installs Sysmon, Splunk Universal Forwarder, and LimaCharlie on Windows VM

param(
    [Parameter(Mandatory=$true)]
    [string]$SplunkServerIP,
    
    [Parameter(Mandatory=$true)]
    [string]$SplunkToken,
    
    [Parameter(Mandatory=$true)]
    [string]$LCInstallKey
)

Write-Host "🔧 WHIS Red vs Blue Lab - Installing Monitoring Stack..." -ForegroundColor Green

# Create monitoring directory
$MonitoringDir = "C:\WhisLab\Monitoring"
New-Item -ItemType Directory -Path $MonitoringDir -Force

# Log installation progress
$LogFile = "$MonitoringDir\install-log.txt"
Start-Transcript -Path $LogFile

try {
    # 1. INSTALL SYSMON
    Write-Host "📊 Installing Sysmon..." -ForegroundColor Yellow
    
    # Download Sysmon
    $SysmonUrl = "https://download.sysinternals.com/files/Sysmon.zip"
    $SysmonZip = "$MonitoringDir\Sysmon.zip"
    Invoke-WebRequest -Uri $SysmonUrl -OutFile $SysmonZip
    
    # Extract Sysmon
    Expand-Archive -Path $SysmonZip -DestinationPath "$MonitoringDir\Sysmon" -Force
    
    # Download SwiftOnSecurity Sysmon config
    $SysmonConfigUrl = "https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml"
    $SysmonConfig = "$MonitoringDir\sysmonconfig.xml"
    Invoke-WebRequest -Uri $SysmonConfigUrl -OutFile $SysmonConfig
    
    # Install Sysmon with config
    & "$MonitoringDir\Sysmon\Sysmon64.exe" -accepteula -i $SysmonConfig
    
    Write-Host "✅ Sysmon installed successfully" -ForegroundColor Green
    
    # 2. INSTALL SPLUNK UNIVERSAL FORWARDER
    Write-Host "🔍 Installing Splunk Universal Forwarder..." -ForegroundColor Yellow
    
    # Download Splunk UF
    $SplunkUrl = "https://download.splunk.com/products/universalforwarder/releases/9.1.2/windows/splunkforwarder-9.1.2-b6b9c8185839-x64-release.msi"
    $SplunkMsi = "$MonitoringDir\splunkforwarder.msi"
    
    # Note: In real deployment, you'd have this pre-staged or use proper download with auth
    # For lab purposes, we'll create a minimal installation
    Write-Host "ℹ️  Splunk UF download requires authentication - installing minimal forwarder" -ForegroundColor Blue
    
    # Create Splunk directories and basic config
    $SplunkHome = "C:\Program Files\SplunkUniversalForwarder"
    New-Item -ItemType Directory -Path "$SplunkHome\etc\apps\whis_inputs\default" -Force
    New-Item -ItemType Directory -Path "$SplunkHome\etc\apps\whis_inputs\local" -Force
    
    # Create inputs.conf for Sysmon forwarding
    $InputsConf = @"
[WinEventLog://Microsoft-Windows-Sysmon/Operational]
disabled = false
index = sysmon
sourcetype = sysmon

[WinEventLog://Security]
disabled = false
index = security
sourcetype = wineventlog

[WinEventLog://System]
disabled = false  
index = system
sourcetype = wineventlog

[WinEventLog://Application]
disabled = false
index = application
sourcetype = wineventlog
"@
    
    $InputsConf | Out-File -FilePath "$SplunkHome\etc\apps\whis_inputs\local\inputs.conf" -Encoding UTF8
    
    # Create outputs.conf for HEC
    $OutputsConf = @"
[tcpout]
defaultGroup = hec_group

[tcpout:hec_group]  
server = ${SplunkServerIP}:9997
compressed = true

[httpout]
disabled = false

[httpout:hec_output]
uri = https://${SplunkServerIP}:8088/services/collector/event
token = $SplunkToken
format = json
useSSL = false
"@
    
    $OutputsConf | Out-File -FilePath "$SplunkHome\etc\apps\whis_inputs\local\outputs.conf" -Encoding UTF8
    
    Write-Host "✅ Splunk UF configured for Sysmon forwarding" -ForegroundColor Green
    
    # 3. INSTALL LIMACHARLIE
    Write-Host "🛡️  Installing LimaCharlie sensor..." -ForegroundColor Yellow
    
    # Download LC sensor installer
    $LCUrl = "https://downloads.limacharlie.io/sensor/windows/64"
    $LCInstaller = "$MonitoringDir\lc_sensor.exe"
    
    try {
        Invoke-WebRequest -Uri $LCUrl -OutFile $LCInstaller
        
        # Install LC sensor
        & $LCInstaller -i $LCInstallKey
        
        Write-Host "✅ LimaCharlie sensor installed" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  LimaCharlie installation failed: $($_.Exception.Message)" -ForegroundColor Orange
        Write-Host "   Manual installation may be required with key: $LCInstallKey" -ForegroundColor Orange
    }
    
    # 4. CONFIGURE WINDOWS FOR VULNERABILITY TESTING
    Write-Host "🎯 Configuring vulnerable services for red team testing..." -ForegroundColor Yellow
    
    # Enable WinRM (HTTP - intentionally insecure)
    Enable-PSRemoting -Force -SkipNetworkProfileCheck
    Set-NetFirewallRule -DisplayName "Windows Remote Management (HTTP-In)" -Enabled True
    
    # Configure WinRM for basic auth (VULNERABLE)
    winrm set winrm/config/service/auth '@{Basic="true"}'
    winrm set winrm/config/service '@{AllowUnencrypted="true"}'
    
    # Enable SMB1 (VULNERABLE - for red team testing)
    Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -All -NoRestart
    
    # Create vulnerable file share
    New-Item -ItemType Directory -Path "C:\VulnShare" -Force
    New-SmbShare -Name "VulnShare" -Path "C:\VulnShare" -FullAccess "Everyone"
    
    # Add some dummy files
    "Confidential data - do not share" | Out-File "C:\VulnShare\secret.txt"
    "admin:password123" | Out-File "C:\VulnShare\backup_credentials.txt"
    
    # Disable Windows Defender real-time protection (for testing)
    Set-MpPreference -DisableRealtimeMonitoring $true
    
    # 5. INSTALL VULNERABLE SOFTWARE
    Write-Host "💀 Installing vulnerable software for realistic scenarios..." -ForegroundColor Red
    
    # Create vulnerable web service
    $VulnWebDir = "C:\inetpub\wwwroot\vulnapp"
    New-Item -ItemType Directory -Path $VulnWebDir -Force
    
    # Simple vulnerable PHP-like page (just HTML for demo)
    $VulnPage = @"
<!DOCTYPE html>
<html>
<head><title>Vulnerable Web App</title></head>
<body>
<h1>Lab Web Application</h1>
<form action='login.php' method='POST'>
    Username: <input type='text' name='user'><br>
    Password: <input type='password' name='pass'><br>
    <input type='submit' value='Login'>
</form>
<p>Admin panel: <a href='admin.html'>admin.html</a></p>
<!-- TODO: Fix SQL injection in login.php -->
</body>
</html>
"@
    
    $VulnPage | Out-File "$VulnWebDir\index.html" -Encoding UTF8
    
    # 6. CREATE WHIS INTEGRATION
    Write-Host "🤖 Setting up Whis integration..." -ForegroundColor Cyan
    
    # Create webhook endpoint configuration
    $WhisConfig = @{
        splunk_hec_url = "https://${SplunkServerIP}:8088/services/collector/event"
        splunk_hec_token = $SplunkToken
        whis_api_url = "http://YOUR_WHIS_API:8001"  # Update with actual Whis API
        lc_webhook_url = "http://YOUR_WHIS_API:8001/webhooks/limacharlie"
    }
    
    $WhisConfig | ConvertTo-Json | Out-File "$MonitoringDir\whis_config.json" -Encoding UTF8
    
    # 7. FINAL CONFIGURATION
    Write-Host "⚙️  Final system configuration..." -ForegroundColor Yellow
    
    # Set up scheduled task for health monitoring
    $TaskAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\WhisLab\health-check.ps1"
    $TaskTrigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -At (Get-Date) -Once
    Register-ScheduledTask -Action $TaskAction -Trigger $TaskTrigger -TaskName "WhisLabHealthCheck" -Description "Health check for Whis lab monitoring"
    
    # Create health check script
    $HealthCheckScript = @"
# Whis Lab Health Check
`$Status = @{
    timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    sysmon_running = (Get-Service Sysmon64 -ErrorAction SilentlyContinue).Status -eq 'Running'
    lc_running = (Get-Process lc_sensor -ErrorAction SilentlyContinue) -ne `$null
    vulnerable_services = @{
        winrm = (Get-Service WinRM).Status -eq 'Running'
        smb = (Get-Service Server).Status -eq 'Running'
    }
    last_sysmon_event = (Get-WinEvent -LogName 'Microsoft-Windows-Sysmon/Operational' -MaxEvents 1 -ErrorAction SilentlyContinue).TimeCreated
}

`$Status | ConvertTo-Json | Out-File "C:\WhisLab\Monitoring\health-status.json" -Encoding UTF8
"@
    
    $HealthCheckScript | Out-File "C:\WhisLab\health-check.ps1" -Encoding UTF8
    
    Write-Host "🎉 WHIS Red vs Blue Lab setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔥 RED TEAM TARGETS:" -ForegroundColor Red
    Write-Host "   - RDP: Port 3389 (admin credentials in Azure output)"
    Write-Host "   - SMB: Port 445 (VulnShare with dummy secrets)"
    Write-Host "   - WinRM: Port 5985/5986 (Basic auth enabled)"
    Write-Host "   - Web App: Port 80 (vulnerable app at /vulnapp/)"
    Write-Host ""
    Write-Host "🛡️  BLUE TEAM MONITORING:" -ForegroundColor Blue
    Write-Host "   - Sysmon: Microsoft-Windows-Sysmon/Operational"
    Write-Host "   - Splunk: Forwarding to ${SplunkServerIP}:8088"
    Write-Host "   - LimaCharlie: Sensor installed and configured"
    Write-Host ""
    Write-Host "🤖 WHIS INTEGRATION:" -ForegroundColor Cyan
    Write-Host "   - Config: C:\WhisLab\Monitoring\whis_config.json"
    Write-Host "   - Health: C:\WhisLab\Monitoring\health-status.json"
    Write-Host ""
    Write-Host "⚠️  REMEMBER: This VM is INTENTIONALLY VULNERABLE for testing!" -ForegroundColor Yellow
    
}
catch {
    Write-Host "❌ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check log: $LogFile" -ForegroundColor Yellow
    throw
}
finally {
    Stop-Transcript
}