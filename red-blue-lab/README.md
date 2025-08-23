# 🎯 WHIS Red vs Blue Training Lab

## 🚀 **READY TO DEPLOY** - Production Configuration

This lab uses your **actual LinkOps Azure subscription** and is ready for immediate deployment.

### **📋 WHAT'S CONFIGURED**
- ✅ **Azure Subscription**: e864a989-7282-4f8e-8ded-2b68911dcc95
- ✅ **Resource Group**: linkops-rg (existing)
- ✅ **Region**: East US  
- ✅ **Service Principal**: Pre-configured
- ✅ **Container Registry**: jimmie012506

## 🔧 **BEFORE YOU DEPLOY**

### **1. Update IP Addresses**
Edit `terraform.tfvars`:
```hcl
# ⚠️ CHANGE THESE TO ACTUAL IPs
attacker_ip = "YOUR_COWORKER_IP/32"  # Red team IP
soc_ip      = "YOUR_IP/32"           # Your IP for monitoring
```

### **2. Add Monitoring Tokens**
```hcl
# ⚠️ GET THESE FROM YOUR SPLUNK/LIMACHARLIE
splunk_hec_token = "your-real-hec-token"
lc_install_key   = "your-real-lc-sensor-key"
```

## ⚡ **DEPLOY IN 3 COMMANDS**

```bash
# 1. Navigate to the lab directory
cd red-blue-lab

# 2. Update your IP addresses and tokens in terraform.tfvars
nano terraform.tfvars

# 3. Deploy the lab
./deploy_lab.sh
```

## 🎯 **WHAT GETS DEPLOYED**

### **Infrastructure**
- **Windows Server 2019** VM (VULN-WIN-01)
- **Public IP** for red team access
- **Network isolation** (only your IPs allowed)
- **Monitoring stack**: Sysmon + Splunk UF + LimaCharlie

### **Intentionally Vulnerable Configs**
- 🔓 **Weak passwords** for brute force practice
- 🔓 **Open file shares** with sensitive data
- 🔓 **Disabled security features** for exploitation
- 🔓 **Decoy credentials** in obvious locations
- 🔓 **Vulnerable services** for lateral movement

## 🔴 **FOR RED TEAM (Your Coworker)**

After deployment, you'll get:
```
🖥️  VM Public IP: [IP ADDRESS]
👤 Username: whisadmin
🔑 Password: WhisLab2025!SecurePassword
🌐 RDP: mstsc /v:[IP ADDRESS]
```

**Attack Scenarios to Try:**
1. **Brute Force**: Try common passwords against RDP
2. **PowerShell**: Run encoded commands for evasion
3. **Persistence**: Add registry keys for startup
4. **Lateral Movement**: Discover shared folders
5. **Data Exfil**: Find and extract "sensitive" files

## 🔵 **FOR BLUE TEAM (You)**

**Monitoring Dashboards:**
- **Splunk**: Monitor `index=whis_lab` for all events
- **LimaCharlie**: Watch EDR detections in real-time
- **Windows Event Logs**: Security, Sysmon, PowerShell

**Expected Detections:**
- Event 4625: Failed RDP attempts
- Event 4624: Successful logons
- Sysmon Event 1: Process creation
- PowerShell Event 4103: Script block logging
- Custom LC rules: Suspicious behavior

## 🤖 **FOR AI TRAINING**

The lab automatically:
- **Correlates** attack events into chains
- **Maps** to MITRE ATT&CK techniques  
- **Generates** training examples for Whis
- **Feeds** attack chains to model retraining

## 💰 **COST CONTROL**

**Estimated Azure Costs:**
- **VM**: ~$50/month (Standard_D2s_v3)
- **Storage**: ~$5/month  
- **Networking**: ~$2/month
- **Total**: ~$57/month

**Cost Saving Tips:**
```bash
# Stop VM when not training (saves ~80% of costs)
az vm deallocate --resource-group linkops-rg --name whis-lab-vuln-vm

# Destroy entire lab when done
./destroy_lab.sh
```

## 🛡️ **SECURITY NOTES**

### **⚠️ THIS SYSTEM IS INTENTIONALLY VULNERABLE**
- **Purpose**: Training only - never production use
- **Isolation**: Network access limited to your IPs only
- **Monitoring**: All activity logged for security awareness
- **Cleanup**: Use `./destroy_lab.sh` when finished

### **What Makes It Vulnerable:**
- Weak password policy (1 character minimum)
- Disabled Windows Defender
- Open SMB shares with "Everyone" access
- Fake sensitive files for red team discovery
- No network segmentation within lab
- Permissive firewall rules for internal traffic

## 📊 **SUCCESS METRICS**

After successful attacks, you should see:
- ✅ **Splunk events** from all attack phases
- ✅ **LimaCharlie detections** triggering
- ✅ **Whis enrichment** of security events  
- ✅ **Training data** generated automatically
- ✅ **Model improvements** from real attack patterns

## 🚨 **TROUBLESHOOTING**

### **Common Issues:**
1. **"IP not allowed"** → Update `attacker_ip` in terraform.tfvars
2. **"Authentication failed"** → Check Azure credentials in .env
3. **"VM not responding"** → Check NSG rules allow your IP
4. **"No monitoring data"** → Verify HEC token and LC key

### **Support:**
- **Terraform errors**: Check Azure permissions
- **VM access**: Verify IP allowlist configuration  
- **Monitoring issues**: Validate Splunk/LC tokens
- **Cost concerns**: Use `az vm deallocate` when not training

---

## 🎯 **READY TO START RED VS BLUE BATTLE?**

Your lab is production-ready with your actual Azure subscription. Update the IP addresses and tokens, then run `./deploy_lab.sh` to begin training!