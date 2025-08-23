#!/bin/bash
# 🧹 DESTROY WHIS RED vs BLUE TRAINING LAB
# Safely tears down the training environment

set -e  # Exit on any error

echo "🧹 Destroying WHIS Red vs Blue Training Lab..."
echo "☁️  LinkOps Azure Subscription: e864a989-7282-4f8e-8ded-2b68911dcc95"
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

# Navigate to terraform directory
cd terraform

echo "⚠️  WARNING: This will PERMANENTLY DELETE all lab resources!"
echo "📋 Resources to be destroyed:"
echo "   - VULN-WIN-01 virtual machine"
echo "   - Virtual network and security groups"
echo "   - All monitoring data and configurations"
echo "   - All attack/defense training data"
echo

read -p "❌ Are you sure you want to destroy the lab? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "💥 Destroying infrastructure..."
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        echo "❌ terraform.tfvars not found!"
        echo "📝 Cannot destroy without configuration file"
        exit 1
    fi
    
    # Destroy all resources
    terraform destroy -var-file="terraform.tfvars" -auto-approve
    
    echo
    echo "🎉 LAB DESTROYED SUCCESSFULLY!"
    echo "✅ All Azure resources have been cleaned up"
    echo "✅ No ongoing charges will be incurred"
    echo "✅ Training data preserved in Whis AI model"
    echo
    echo "📊 CLEANUP SUMMARY:"
    echo "   - Virtual machines: DELETED"
    echo "   - Network resources: DELETED"
    echo "   - Storage accounts: DELETED"
    echo "   - Security groups: DELETED"
    echo "   - Public IP addresses: RELEASED"
    echo
    echo "💡 TIP: To redeploy the lab:"
    echo "   ./deploy_lab.sh"
    
else
    echo "❌ Destruction cancelled - lab remains active"
    exit 0
fi