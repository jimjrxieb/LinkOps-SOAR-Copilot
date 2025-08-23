terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    virtual_machine {
      delete_os_disk_on_deletion = true
      graceful_shutdown         = false
      skip_shutdown_and_force_delete = true
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "whis_lab" {
  name     = var.resource_group_name
  location = var.location
  
  tags = {
    Environment = "Lab"
    Purpose     = "WHIS Red vs Blue Testing"
    Owner       = "SecOps"
    Terraform   = "true"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "lab_network" {
  name                = "${var.prefix}-vnet"
  address_space       = ["10.10.0.0/16"]
  location            = azurerm_resource_group.whis_lab.location
  resource_group_name = azurerm_resource_group.whis_lab.name
  
  tags = {
    Environment = "Lab"
  }
}

# Subnet for vulnerable systems
resource "azurerm_subnet" "vulnerable_subnet" {
  name                 = "vulnerable-subnet"
  resource_group_name  = azurerm_resource_group.whis_lab.name
  virtual_network_name = azurerm_virtual_network.lab_network.name
  address_prefixes     = ["10.10.1.0/24"]
}

# Subnet for monitoring systems
resource "azurerm_subnet" "monitoring_subnet" {
  name                 = "monitoring-subnet"
  resource_group_name  = azurerm_resource_group.whis_lab.name
  virtual_network_name = azurerm_virtual_network.lab_network.name
  address_prefixes     = ["10.10.2.0/24"]
}

# Network Security Group - Vulnerable (INTENTIONALLY WEAK)
resource "azurerm_network_security_group" "vulnerable_nsg" {
  name                = "${var.prefix}-vulnerable-nsg"
  location            = azurerm_resource_group.whis_lab.location
  resource_group_name = azurerm_resource_group.whis_lab.name
  
  # WARNING: Intentionally vulnerable for red team testing
  security_rule {
    name                       = "AllowRDP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefix      = var.attacker_ip  # Red team IP
    destination_address_prefix = "*"
  }
  
  security_rule {
    name                       = "AllowSMB"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "445"
    source_address_prefix      = "10.10.0.0/16"
    destination_address_prefix = "*"
  }
  
  security_rule {
    name                       = "AllowWinRM"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5985-5986"
    source_address_prefix      = "10.10.0.0/16"
    destination_address_prefix = "*"
  }
  
  tags = {
    Environment = "Lab"
    Security    = "INTENTIONALLY_VULNERABLE"
  }
}

# Network Security Group - Monitoring (SECURE)
resource "azurerm_network_security_group" "monitoring_nsg" {
  name                = "${var.prefix}-monitoring-nsg"
  location            = azurerm_resource_group.whis_lab.location
  resource_group_name = azurerm_resource_group.whis_lab.name
  
  security_rule {
    name                       = "AllowSplunkWeb"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8000"
    source_address_prefix      = var.soc_ip  # SOC analyst IP
    destination_address_prefix = "*"
  }
  
  security_rule {
    name                       = "AllowSplunkHEC"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8088"
    source_address_prefix      = "10.10.0.0/16"
    destination_address_prefix = "*"
  }
  
  tags = {
    Environment = "Lab"
  }
}

# Associate NSGs with subnets
resource "azurerm_subnet_network_security_group_association" "vulnerable_subnet_nsg" {
  subnet_id                 = azurerm_subnet.vulnerable_subnet.id
  network_security_group_id = azurerm_network_security_group.vulnerable_nsg.id
}

resource "azurerm_subnet_network_security_group_association" "monitoring_subnet_nsg" {
  subnet_id                 = azurerm_subnet.monitoring_subnet.id
  network_security_group_id = azurerm_network_security_group.monitoring_nsg.id
}

# Public IP for vulnerable VM (for red team access)
resource "azurerm_public_ip" "vulnerable_vm_pip" {
  name                = "${var.prefix}-vulnerable-pip"
  location            = azurerm_resource_group.whis_lab.location
  resource_group_name = azurerm_resource_group.whis_lab.name
  allocation_method   = "Static"
  sku                 = "Standard"
  
  tags = {
    Environment = "Lab"
    Purpose     = "Red Team Target"
  }
}

# Network Interface for Vulnerable Windows VM
resource "azurerm_network_interface" "vulnerable_vm_nic" {
  name                = "${var.prefix}-vulnerable-nic"
  location            = azurerm_resource_group.whis_lab.location
  resource_group_name = azurerm_resource_group.whis_lab.name
  
  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.vulnerable_subnet.id
    private_ip_address_allocation = "Static"
    private_ip_address            = "10.10.1.10"
    public_ip_address_id          = azurerm_public_ip.vulnerable_vm_pip.id
  }
  
  tags = {
    Environment = "Lab"
  }
}

# Random password for vulnerable VM (intentionally weak for demo)
resource "random_password" "vulnerable_vm_password" {
  length  = 12
  special = true
  upper   = true
  lower   = true
  numeric = true
}

# Vulnerable Windows VM
resource "azurerm_windows_virtual_machine" "vulnerable_vm" {
  name                = "${var.prefix}-vuln-vm"
  computer_name       = "VULN-WIN-01"
  resource_group_name = azurerm_resource_group.whis_lab.name
  location            = azurerm_resource_group.whis_lab.location
  size                = var.vm_size
  admin_username      = var.admin_username
  admin_password      = random_password.vulnerable_vm_password.result
  
  network_interface_ids = [
    azurerm_network_interface.vulnerable_vm_nic.id,
  ]
  
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }
  
  source_image_reference {
    publisher = "MicrosoftWindowsServer"
    offer     = "WindowsServer"
    sku       = "2019-Datacenter"
    version   = "latest"
  }
  
  # Enable vulnerable services
  winrm_listener {
    protocol = "Http"
  }
  
  tags = {
    Environment = "Lab"
    Purpose     = "Red Team Target"
    Security    = "INTENTIONALLY_VULNERABLE"
    Monitoring  = "Sysmon+Splunk+LimaCharlie"
  }
}

# VM Extension - Install monitoring tools
resource "azurerm_virtual_machine_extension" "install_monitoring" {
  name                 = "InstallMonitoring"
  virtual_machine_id   = azurerm_windows_virtual_machine.vulnerable_vm.id
  publisher            = "Microsoft.Compute"
  type                 = "CustomScriptExtension"
  type_handler_version = "1.10"
  
  settings = jsonencode({
    fileUris = [
      "https://raw.githubusercontent.com/linkops-industries/SOAR-copilot/main/infrastructure/scripts/install-monitoring.ps1"
    ]
  })
  
  protected_settings = jsonencode({
    commandToExecute = "powershell -ExecutionPolicy Unrestricted -File install-monitoring.ps1 -SplunkServerIP ${var.splunk_server_ip} -SplunkToken ${var.splunk_hec_token} -LCInstallKey ${var.lc_install_key}"
  })
  
  tags = {
    Purpose = "Monitoring Installation"
  }
}

# Outputs
output "vulnerable_vm_public_ip" {
  value       = azurerm_public_ip.vulnerable_vm_pip.ip_address
  description = "Public IP of vulnerable Windows VM for red team access"
  sensitive   = false
}

output "vulnerable_vm_private_ip" {
  value       = azurerm_network_interface.vulnerable_vm_nic.ip_configuration[0].private_ip_address
  description = "Private IP of vulnerable Windows VM"
}

output "admin_username" {
  value       = var.admin_username
  description = "Admin username for RDP access"
}

output "admin_password" {
  value       = random_password.vulnerable_vm_password.result
  description = "Admin password for RDP access"
  sensitive   = true
}

output "connection_string" {
  value       = "RDP to ${azurerm_public_ip.vulnerable_vm_pip.ip_address} with ${var.admin_username}"
  description = "Connection string for red team"
}