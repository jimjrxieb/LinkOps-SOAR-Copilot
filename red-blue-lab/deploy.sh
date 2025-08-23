#!/bin/bash
# WHIS Red vs Blue Lab Deployment Script

set -e

echo "🚀 WHIS Red vs Blue Lab Deployment"
echo "=================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install: https://www.terraform.io/downloads"
    exit 1
fi

# Check if logged into Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please run 'az login'"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Check for terraform.tfvars
if [ ! -f "terraform/terraform.tfvars" ]; then
    echo "⚠️  terraform.tfvars not found. Creating from example..."
    cp terraform/terraform.tfvars.example terraform/terraform.tfvars
    echo "❗ IMPORTANT: Update terraform/terraform.tfvars with your values before continuing!"
    echo "   Required updates:"
    echo "   - attacker_ip: Your coworker's IP address"
    echo "   - soc_ip: Your IP address"
    echo "   - splunk_hec_token: Get from Splunk"
    echo "   - lc_install_key: Get from LimaCharlie"
    echo ""
    read -p "Press Enter after updating terraform.tfvars..."
fi

cd terraform

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Validate configuration
echo "✅ Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "📋 Creating deployment plan..."
terraform plan -out=tfplan

echo ""
echo "🎯 RED VS BLUE LAB DEPLOYMENT PLAN"
echo "================================="
echo ""
echo "This will create:"
echo "  🎯 1x Vulnerable Windows VM (intentionally weak security)"
echo "  📊 Sysmon + Splunk Universal Forwarder"  
echo "  🛡️  LimaCharlie EDR sensor"
echo "  🌐 Virtual network with vulnerable + monitoring subnets"
echo "  🚨 Network Security Groups (NSGs) - vulnerable allows RDP/SMB/WinRM"
echo "  🔗 Integration points for Whis SOAR-Copilot"
echo ""
echo "⚠️  WARNING: This VM will be INTENTIONALLY VULNERABLE for red team testing!"
echo "   - Weak passwords, open services, disabled security features"
echo "   - Only deploy in isolated lab environment"
echo "   - Do not connect to production networks"
echo ""

read -p "Deploy the lab? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Deploy infrastructure
echo "🚀 Deploying infrastructure..."
terraform apply tfplan

# Get outputs
echo ""
echo "📊 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""

VULNERABLE_IP=$(terraform output -raw vulnerable_vm_public_ip)
ADMIN_USERNAME=$(terraform output -raw admin_username)
ADMIN_PASSWORD=$(terraform output -raw admin_password)

echo "🎯 RED TEAM TARGET INFORMATION:"
echo "   IP Address: $VULNERABLE_IP"
echo "   Username: $ADMIN_USERNAME"
echo "   Password: $ADMIN_PASSWORD"
echo "   RDP: mstsc /v:$VULNERABLE_IP"
echo ""

echo "🛡️  BLUE TEAM MONITORING:"
echo "   VM Internal IP: $(terraform output -raw vulnerable_vm_private_ip)"
echo "   Sysmon Logs: Microsoft-Windows-Sysmon/Operational"
echo "   Health Check: C:\\WhisLab\\Monitoring\\health-status.json"
echo ""

echo "🤖 WHIS INTEGRATION:"
echo "   Update your Whis API config with VM IP: $VULNERABLE_IP"
echo "   Webhook endpoints configured for Splunk HEC forwarding"
echo "   LimaCharlie will send detections to configured webhook"
echo ""

echo "🔥 BATTLE PLAN:"
echo "   1. Red team attacks: $VULNERABLE_IP"
echo "   2. Blue team monitors: Sysmon + Splunk + LimaCharlie"  
echo "   3. Whis analyzes: Security events → SOAR recommendations"
echo "   4. Learn and improve: Retrain based on attack patterns"
echo ""

echo "⚠️  SECURITY REMINDER:"
echo "   - This is a lab environment only"
echo "   - VM is intentionally vulnerable"  
echo "   - Destroy when testing complete: 'terraform destroy'"
echo ""

echo "🎉 Lab is ready for red vs blue testing!"

# Save connection info
cat > ../connection_info.txt << EOF
WHIS Red vs Blue Lab - Connection Information
=============================================

RED TEAM ACCESS:
IP: $VULNERABLE_IP
Username: $ADMIN_USERNAME  
Password: $ADMIN_PASSWORD
RDP Command: mstsc /v:$VULNERABLE_IP

BLUE TEAM MONITORING:
Internal IP: $(terraform output -raw vulnerable_vm_private_ip)
Sysmon: Microsoft-Windows-Sysmon/Operational
Splunk: Configured for HEC forwarding
LimaCharlie: Sensor installed

VULNERABLE SERVICES:
- RDP (3389): Enabled with weak password
- SMB (445): File share "VulnShare" with dummy secrets  
- WinRM (5985/5986): Basic auth enabled
- Web App (80): Vulnerable app at /vulnapp/

WHIS INTEGRATION POINTS:
- Splunk HEC: Events forward to Whis for analysis
- LimaCharlie: Detections webhook to Whis API
- Health Monitor: C:\WhisLab\Monitoring\health-status.json

Generated: $(date)
EOF

echo "📄 Connection info saved to: ../connection_info.txt"