resource "hcloud_ssh_key" "operator" {
  name       = "${var.service_name}-operator"
  public_key = var.ssh_public_key
}
resource "hcloud_network" "control" {
  name     = var.service_name
  ip_range = var.network_cidr
}
resource "hcloud_network_subnet" "control" {
  network_id   = hcloud_network.control.id
  type         = "cloud"
  network_zone = "eu-central"
  ip_range     = var.network_cidr
}
resource "hcloud_firewall" "state" {
  name = var.service_name
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = var.admin_cidrs
  }
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}
resource "hcloud_server" "state" {
  name               = var.service_name
  image              = tostring(var.image_id)
  server_type        = "cx23"
  location           = var.location
  ssh_keys           = [hcloud_ssh_key.operator.id]
  firewall_ids       = [hcloud_firewall.state.id]
  delete_protection  = true
  rebuild_protection = true
  backups            = false
  network {
    network_id = hcloud_network.control.id
    ip         = cidrhost(var.network_cidr, 2)
  }
  depends_on = [hcloud_network_subnet.control]
  lifecycle {
    prevent_destroy = true
  }
}
resource "hcloud_volume" "state" {
  name              = "${var.service_name}-postgres"
  size              = 10
  location          = var.location
  delete_protection = true
  lifecycle {
    prevent_destroy = true
  }
}
resource "hcloud_volume_attachment" "state" {
  server_id = hcloud_server.state.id
  volume_id = hcloud_volume.state.id
  automount = false
}
output "state_host" {
  value = hcloud_server.state.ipv4_address
}
output "state_device" {
  value = "/dev/disk/by-id/scsi-0HC_Volume_${hcloud_volume.state.id}"
}
output "operator_manifest" {
  value = {
    device          = "/dev/disk/by-id/scsi-0HC_Volume_${hcloud_volume.state.id}"
    hostname        = var.state_hostname
    location        = var.location
    backup_location = var.backup_location
    backup_bucket   = var.bucket_name
    admin_cidrs     = sort(tolist(var.admin_cidrs))
  }
}
