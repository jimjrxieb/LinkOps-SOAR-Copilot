#!/bin/bash
# 🎯 WHIS RED vs BLUE TRAINING LAB DEPLOYMENT
# Uses your actual LinkOps Azure subscription and credentials

set -e  # Exit on any error

echo "🎯 Deploying WHIS Red vs Blue Training Lab..."
echo "☁️  Using LinkOps Azure Subscription: e864a989-7282-4f8e-8ded-2b68911dcc95"
echo "📍 Resource Group: linkops-rg"
echo

# Load environment variables
if [ -f .env ]; then
    echo "📂 Loading Azure credentials from .env file..."
    source .env
else
    echo "⚠️  No .env file found. Please create one with your Azure credentials."
    exit 1
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install: https://terraform.io/downloads"
    exit 1
fi

if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

echo "✅ Prerequisites satisfied"
echo

# Navigate to terraform directory
cd terraform

# Initialize Terraform
echo "🏗️  Initializing Terraform with LinkOps backend..."
terraform init

# Validate configuration
echo "🔍 Validating Terraform configuration..."
terraform validate

# Show plan
echo "📋 DEPLOYMENT PLAN:"
echo "✅ Using existing resource group: linkops-rg"
echo "✅ Vulnerable Windows VM (VULN-WIN-01)"
echo "✅ Sysmon + Splunk UF + LimaCharlie monitoring"
echo "✅ Network isolation with attacker IP allowlist"
echo "✅ Intentionally vulnerable configurations for training"
echo "✅ Decoy files and weak passwords for red team practice"
echo

echo "⚠️  SECURITY NOTICE:"
echo "🎯 This creates an INTENTIONALLY VULNERABLE system"
echo "🔒 Only for red vs blue team training"
echo "📍 Deployed to LinkOps Azure subscription"
echo

read -p "🚀 Deploy the training lab? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "⚡ Deploying infrastructure to Azure..."
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        echo "❌ terraform.tfvars not found!"
        echo "📝 Please copy terraform.tfvars.example to terraform.tfvars and update:"
        echo "   - attacker_ip (your coworker's IP)"
        echo "   - splunk_hec_token"
        echo "   - lc_install_key"
        exit 1
    fi
    
    # Apply configuration
    terraform apply -var-file="terraform.tfvars" -auto-approve
    
    echo
    echo "🎉 RED VS BLUE LAB DEPLOYED SUCCESSFULLY!"
    echo
    echo "📋 NEXT STEPS:"
    echo "1. 🔴 Red Team: RDP to the provided IP address"
    echo "2. 🔵 Blue Team: Monitor Splunk and LimaCharlie for detections"
    echo "3. 🤖 AI Training: Attack chains automatically feed Whis training"
    echo "4. 🎯 Practice: Run attack scenarios, validate detections"
    echo
    
    echo "📊 CONNECTION DETAILS:"
    terraform output -json | jq -r '
        "🖥️  VM Public IP: " + .vulnerable_vm_public_ip.value,
        "👤 Username: " + .admin_username.value,
        "🔑 Password: " + .admin_password.value,
        "🌐 Connection: RDP to " + .vulnerable_vm_public_ip.value
    '
    
    echo
    echo "⚠️  REMEMBER:"
    echo "🛡️  This system is INTENTIONALLY VULNERABLE - training use only"
    echo "🔒 Network access restricted to configured attacker IP"
    echo "📊 All activity monitored and logged for Whis training"
    
else
    echo "❌ Deployment cancelled"
    exit 0
fi

echo
echo "💡 TIP: To destroy the lab when done:"
echo "   ./destroy_lab.sh"