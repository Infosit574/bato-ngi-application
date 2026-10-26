mock_provider "hcloud" {}
mock_provider "aws" {}
run "example" {
  command = plan
  assert {
    condition     = hcloud_server.state.delete_protection && hcloud_volume.state.delete_protection && !hcloud_volume_attachment.state.automount
    error_message = "The independent service and its unformatted disk must be protected."
  }
  assert {
    condition     = alltrue([for rule in hcloud_firewall.state.rule : rule.protocol == "icmp" || rule.port == "22"])
    error_message = "The state PostgreSQL port must never be public."
  }
}
run "public_state_access" {
  command = plan
  variables {
    admin_cidrs = ["0.0.0.0/0", "::/0"]
  }
  expect_failures = [var.admin_cidrs]
}
run "foreign_state" {
  command = plan
  variables {
    location = "hel1"
  }
  expect_failures = [var.location]
}
