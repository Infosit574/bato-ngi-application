locals {
  name   = "${var.tenant}-${var.environment}"
  labels = { tenant = var.tenant, environment = var.environment, managed_by = "bato" }
}

resource "hcloud_ssh_key" "operator" {
  name       = "${local.name}-operator"
  public_key = var.ssh_public_key
  labels     = local.labels
}
resource "hcloud_network" "node" {
  name     = local.name
  ip_range = var.network_cidr
  labels   = local.labels
}
resource "hcloud_network_subnet" "node" {
  network_id   = hcloud_network.node.id
  type         = "cloud"
  network_zone = "eu-central"
  ip_range     = var.network_cidr
}
resource "hcloud_firewall" "node" {
  name   = local.name
  labels = local.labels
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = var.admin_cidrs
  }
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = setunion(var.admin_cidrs, var.tenant_cidrs)
  }
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}
data "hcloud_volume" "postgres" {
  id       = var.volume_id
  location = var.location
}
resource "hcloud_server" "node" {
  name         = local.name
  image        = tostring(var.image_id)
  server_type  = var.server_type
  location     = var.location
  ssh_keys     = [hcloud_ssh_key.operator.id]
  firewall_ids = [hcloud_firewall.node.id]
  labels       = merge(local.labels, { source_commit = var.source_commit })
  backups      = false
  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
  network {
    network_id = hcloud_network.node.id
    ip         = cidrhost(var.network_cidr, 2)
  }
  depends_on = [hcloud_network_subnet.node]
  lifecycle {
    precondition {
      condition = alltrue([
        data.hcloud_volume.postgres.name == var.volume_name,
        data.hcloud_volume.postgres.location == var.location,
        lookup(data.hcloud_volume.postgres.labels, "tenant", null) == var.tenant,
        lookup(data.hcloud_volume.postgres.labels, "environment", null) == var.environment,
        data.hcloud_volume.postgres.delete_protection
      ])
      error_message = "Retained disk identity, location, or protection does not match this node."
    }
  }
}
resource "hcloud_volume_attachment" "postgres" {
  volume_id = var.volume_id
  server_id = hcloud_server.node.id
  automount = false
}
resource "hcloud_zone_rrset" "ipv4" {
  zone    = var.zone_name
  name    = var.record_name
  type    = "A"
  ttl     = 300
  records = [{ value = hcloud_server.node.ipv4_address }]
}
resource "hcloud_zone_rrset" "ipv6" {
  zone    = var.zone_name
  name    = var.record_name
  type    = "AAAA"
  ttl     = 300
  records = [{ value = hcloud_server.node.ipv6_address }]
}

output "operator_manifest" {
  value = {
    tenant          = var.tenant
    location        = var.location
    backup_location = var.backup_location
    backup_bucket   = var.backup_bucket
    environment     = var.environment
    source_commit   = var.source_commit
    volume_id       = var.volume_id
    volume_name     = var.volume_name
    device          = "/dev/disk/by-id/scsi-0HC_Volume_${var.volume_id}"
    node_fqdn       = var.node_fqdn
    acme_email      = var.acme_email
    admin_cidrs     = sort(tolist(var.admin_cidrs))
    tenant_cidrs    = sort(tolist(setunion(var.admin_cidrs, var.tenant_cidrs)))
    ipv4            = hcloud_server.node.ipv4_address
    ipv6            = hcloud_server.node.ipv6_address
  }
}
