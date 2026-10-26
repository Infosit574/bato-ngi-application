mock_provider "hcloud" {}
override_data {
  target = data.hcloud_volume.postgres
  values = {
    name              = "example-dev-postgres"
    labels            = { tenant = "example", environment = "dev" }
    delete_protection = true
  }
}
run "example_dev" {
  command = plan
  variables {
    environment     = "dev"
    server_type     = "cx23"
    location        = "fsn1"
    backup_location = "nbg1"
    volume_name     = "example-dev-postgres"
  }
  override_data {
    target = data.hcloud_volume.postgres
    values = {
      name              = "example-dev-postgres"
      labels            = { tenant = "example", environment = "dev" }
      delete_protection = true
    }
  }
  assert {
    condition     = hcloud_server.node.name == "example-${var.environment}" && hcloud_volume_attachment.postgres.volume_id == var.volume_id
    error_message = "Environment identity and retained disk attachment must be preserved."
  }
  assert {
    condition     = hcloud_server.node.user_data == null && hcloud_volume_attachment.postgres.automount == false
    error_message = "Never inject secrets or format/mount automatically."
  }
  assert {
    condition     = alltrue([for rule in hcloud_firewall.node.rule : rule.protocol == "icmp" || contains(["22", "443"], rule.port)])
    error_message = "Only SSH and HTTPS may be public TCP ingress."
  }
}
run "example_prod" {
  command = plan
  variables {
    environment     = "prod"
    server_type     = "cx33"
    location        = "nbg1"
    backup_location = "fsn1"
    volume_name     = "example-prod-postgres"
  }
  override_data {
    target = data.hcloud_volume.postgres
    values = {
      name              = "example-prod-postgres"
      labels            = { tenant = "example", environment = "prod" }
      delete_protection = true
    }
  }
  assert {
    condition     = hcloud_server.node.name == "example-prod" && hcloud_server.node.server_type == "cx33"
    error_message = "Production must remain a separate CX33 node."
  }
}
run "open_ingress" {
  command = plan
  variables {
    admin_cidrs = ["0.0.0.0/0", "::/0"]
  }
  expect_failures = [var.admin_cidrs]
}
run "empty_ingress" {
  command = plan
  variables {
    tenant_cidrs = []
  }
  expect_failures = [var.tenant_cidrs]
}
run "foreign_location" {
  command = plan
  variables {
    location = "hel1"
  }
  expect_failures = [var.location]
}
run "unapproved_source" {
  command = plan
  variables {
    source_commit = "main"
  }
  expect_failures = [var.source_commit]
}
run "wrong_environment_disk" {
  command = plan
  override_data {
    target = data.hcloud_volume.postgres
    values = {
      name     = "other-tenant-postgres"
      location = "fsn1"
    }
  }
  expect_failures = [hcloud_server.node]
}
