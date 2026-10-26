variable "service_name" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,40}$", var.service_name))
    error_message = "Supply an independent state service name."
  }
}
variable "state_hostname" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9.-]+$", var.state_hostname))
    error_message = "Supply the operator-CA state certificate hostname."
  }
}
variable "backup_location" {
  type = string
  validation {
    condition     = contains(["fsn1", "nbg1"], var.backup_location) && var.backup_location != var.location
    error_message = "State backups must use the other German location."
  }
}
variable "bucket_name" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "Use a unique private backup bucket name."
  }
}
variable "state_principal" {
  type = string
}
variable "retention_principal" {
  type = string
}
variable "owner_principal" {
  type = string
  validation {
    condition = length(toset([var.state_principal, var.retention_principal, var.owner_principal])) == 3 && alltrue([
      for p in [var.state_principal, var.retention_principal, var.owner_principal] : can(regex("^arn:aws:iam:::user/p[0-9]+:[A-Za-z0-9]+$", p))
    ])
    error_message = "Use three independent public Hetzner S3 key ARNs."
  }
}
variable "location" {
  type = string
  validation {
    condition     = contains(["fsn1", "nbg1"], var.location)
    error_message = "State must remain in Germany."
  }
}
variable "image_id" {
  type = number
  validation {
    condition     = var.image_id > 0 && floor(var.image_id) == var.image_id
    error_message = "Supply a verified Debian 12 x86 image ID."
  }
}
variable "ssh_public_key" {
  type = string
  validation {
    condition     = startswith(var.ssh_public_key, "ssh-ed25519 ")
    error_message = "Supply an Ed25519 operator public key."
  }
}
variable "admin_cidrs" {
  type = set(string)
  validation {
    condition = length(var.admin_cidrs) >= 2 && alltrue([
      for c in var.admin_cidrs : can(cidrhost(c, 0)) && try(tonumber(split("/", c)[1]) > 0, false)
    ]) && anytrue([for c in var.admin_cidrs : strcontains(c, ":")]) && anytrue([for c in var.admin_cidrs : !strcontains(c, ":")])
    error_message = "Supply non-global IPv4 and IPv6 operator SSH CIDRs."
  }
}
variable "network_cidr" {
  type = string
  validation {
    condition     = can(cidrhost(var.network_cidr, 2)) && !strcontains(var.network_cidr, ":")
    error_message = "Supply a separate IPv4 control network."
  }
}
