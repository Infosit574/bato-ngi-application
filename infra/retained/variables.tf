variable "tenant" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.tenant))
    error_message = "Use a lowercase tenant slug."
  }
}
variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}
variable "location" {
  type = string
  validation {
    condition     = contains(["fsn1", "nbg1"], var.location)
    error_message = "Disk must remain in Germany."
  }
}
variable "backup_location" {
  type = string
  validation {
    condition     = contains(["fsn1", "nbg1"], var.backup_location) && var.backup_location != var.location
    error_message = "Backups must use the other German location."
  }
}
variable "volume_size" {
  type = number
  validation {
    condition     = var.volume_size >= (var.environment == "prod" ? 100 : 20)
    error_message = "Disk minimum is 20 GB dev, 100 GB prod."
  }
}
variable "bucket_name" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "Use a unique 3–63 character bucket name."
  }
}
variable "node_principal" {
  description = "Public Hetzner S3 user ARN for a key in a separate credentials project. No secret key."
  type        = string
  validation {
    condition     = can(regex("^arn:aws:iam:::user/p[0-9]+:[A-Za-z0-9]+$", var.node_principal))
    error_message = "Use Hetzner's per-key pPROJECT:ACCESSKEY ARN, not an AWS account ARN."
  }
}
variable "retention_principal" {
  description = "Independent off-node retention key ARN."
  type        = string
  validation {
    condition     = can(regex("^arn:aws:iam:::user/p[0-9]+:[A-Za-z0-9]+$", var.retention_principal)) && var.retention_principal != var.node_principal
    error_message = "Use a distinct off-node Hetzner retention principal."
  }
}
variable "owner_principal" {
  description = "Offline bucket owner key ARN, never installed on a node."
  type        = string
  validation {
    condition     = can(regex("^arn:aws:iam:::user/p[0-9]+:[A-Za-z0-9]+$", var.owner_principal)) && !contains([var.node_principal, var.retention_principal], var.owner_principal)
    error_message = "Use a distinct offline owner principal."
  }
}
