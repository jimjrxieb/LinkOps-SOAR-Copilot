# Variables for WHIS Red vs Blue Lab Infrastructure

variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "whis-redvsblue-lab"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "prefix" {
  description = "Prefix for resource naming"
  type        = string
  default     = "whis-lab"
}

variable "vm_size" {
  description = "Size of the Windows VM"
  type        = string
  default     = "Standard_D2s_v3"  # 2 vCPU, 8GB RAM
}

variable "admin_username" {
  description = "Admin username for Windows VM"
  type        = string
  default     = "labadmin"
}

variable "attacker_ip" {
  description = "IP address of red team attacker (your coworker's IP)"
  type        = string
  default     = "0.0.0.0/0"  # CHANGE THIS TO YOUR COWORKER'S ACTUAL IP
}

variable "soc_ip" {
  description = "IP address of SOC analyst for monitoring access"
  type        = string
  default     = "0.0.0.0/0"  # CHANGE THIS TO YOUR IP
}

variable "splunk_server_ip" {
  description = "IP address of Splunk server (can be same as vulnerable VM for standalone)"
  type        = string
  default     = "10.10.1.10"
}

variable "splunk_hec_token" {
  description = "Splunk HEC token for log ingestion"
  type        = string
  sensitive   = true
}

variable "lc_install_key" {
  description = "LimaCharlie installation key"
  type        = string
  sensitive   = true
}

# Optional: Add more vulnerable VMs for complex scenarios
variable "additional_vulnerable_vms" {
  description = "Number of additional vulnerable VMs to create"
  type        = number
  default     = 0
}

variable "enable_file_shares" {
  description = "Enable vulnerable SMB file shares"
  type        = bool
  default     = true
}

variable "enable_weak_passwords" {
  description = "Use intentionally weak passwords for demo"
  type        = bool
  default     = true
}

variable "install_vulnerable_software" {
  description = "Install vulnerable software for realistic red team scenarios"
  type        = bool
  default     = true
}

variable "lab_scenario" {
  description = "Lab scenario to deploy (basic, apt, ransomware)"
  type        = string
  default     = "basic"
  
  validation {
    condition     = contains(["basic", "apt", "ransomware", "lateral_movement"], var.lab_scenario)
    error_message = "Lab scenario must be one of: basic, apt, ransomware, lateral_movement."
  }
}