variable "tenant" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.tenant))
    error_message = "Use a lowercase tenant slug."
  }
}
variable "backup_bucket" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.backup_bucket))
    error_message = "Supply this environment's retained backup bucket."
  }
}
variable "backup_location" {
  type = string
  validation {
    condition     = contains(["fsn1", "nbg1"], var.backup_location) && var.backup_location != var.location
    error_message = "Backups must use the other German location."
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
    error_message = "Nodes must remain in Germany."
  }
}
variable "server_type" {
  type = string
  validation {
    condition     = var.server_type == (var.environment == "dev" ? "cx23" : "cx33")
    error_message = "Use CX23 for dev and CX33 for prod."
  }
}
variable "image_id" {
  description = "Operator-verified Debian 12 x86 image ID."
  type        = number
  validation {
    condition     = var.image_id > 0 && floor(var.image_id) == var.image_id
    error_message = "Supply a verified numeric image ID."
  }
}
variable "source_commit" {
  description = "Explicitly approved full Git commit; never inferred from HEAD."
  type        = string
  validation {
    condition     = can(regex("^[0-9a-f]{40}$", var.source_commit))
    error_message = "Approve a full lowercase 40-character source commit."
  }
}
variable "ssh_public_key" {
  type = string
  validation {
    condition     = can(regex("^ssh-ed25519 [A-Za-z0-9+/]+={0,2}( .*)?$", var.ssh_public_key))
    error_message = "Supply an operator Ed25519 public key, never a private key."
  }
}
variable "admin_cidrs" {
  type = set(string)
  validation {
    condition = length(var.admin_cidrs) >= 2 && alltrue([
      for cidr in var.admin_cidrs : can(cidrhost(cidr, 0)) && try(tonumber(split("/", cidr)[1]) > 0, false)
    ]) && anytrue([for c in var.admin_cidrs : !strcontains(c, ":")]) && anytrue([for c in var.admin_cidrs : strcontains(c, ":")])
    error_message = "Supply nonempty, non-global IPv4 and IPv6 admin CIDRs."
  }
}
variable "tenant_cidrs" {
  type = set(string)
  validation {
    condition = length(var.tenant_cidrs) >= 2 && alltrue([
      for cidr in var.tenant_cidrs : can(cidrhost(cidr, 0)) && try(tonumber(split("/", cidr)[1]) > 0, false)
    ]) && anytrue([for c in var.tenant_cidrs : !strcontains(c, ":")]) && anytrue([for c in var.tenant_cidrs : strcontains(c, ":")])
    error_message = "Supply nonempty, non-global IPv4 and IPv6 tenant CIDRs."
  }
}
variable "network_cidr" {
  description = "Dedicated node network; documentation range in examples, RFC1918 for live Hetzner."
  type        = string
  validation {
    condition     = can(cidrhost(var.network_cidr, 2)) && !strcontains(var.network_cidr, ":")
    error_message = "Supply an IPv4 network."
  }
}
variable "volume_id" {
  description = "Retained root output; compute never owns the disk."
  type        = number
}
variable "volume_name" {
  type = string
  validation {
    condition     = var.volume_name == "${var.tenant}-${var.environment}-postgres"
    error_message = "Disk identity must match tenant and environment."
  }
}
variable "zone_name" {
  type = string
}
variable "record_name" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]+$", var.record_name))
    error_message = "Use a relative DNS record name."
  }
}
variable "node_fqdn" {
  type = string
  validation {
    condition     = var.node_fqdn == "${var.record_name}.${var.zone_name}"
    error_message = "FQDN must match the delegated zone and relative record."
  }
}
variable "dns_provider" {
  type = string
  validation {
    condition     = var.dns_provider == "hetzner"
    error_message = "Only the current Hetzner Cloud DNS adapter is implemented."
  }
}
variable "acme_email" {
  type = string
  validation {
    condition     = can(regex("^[^@ ]+@[^@ ]+\\.[^@ ]+$", var.acme_email))
    error_message = "Supply the operator ACME contact."
  }
}
