mock_provider "hcloud" {}
mock_provider "aws" {}
run "example" {
  command = plan
  assert {
    condition     = hcloud_volume.postgres.name == "example-${var.environment}-postgres" && hcloud_volume.postgres.delete_protection
    error_message = "Persistent disk must have environment identity and provider deletion protection."
  }
  assert {
    condition     = !aws_s3_bucket.backup.force_destroy && local.repo_path == "example/${var.environment}/epoch-1"
    error_message = "Never empty the backup bucket on destroy or share repository paths."
  }
  assert {
    condition     = jsondecode(aws_s3_bucket_policy.backup.policy).Statement[1].Effect == "Deny" && contains(jsondecode(aws_s3_bucket_policy.backup.policy).Statement[1].Action, "s3:DeleteObject")
    error_message = "The node must not delete backups."
  }
}
run "foreign_backups" {
  command = plan
  variables {
    backup_location = "hel1"
  }
  expect_failures = [var.backup_location]
}
run "undersized_disk" {
  command = plan
  variables {
    volume_size = 10
  }
  expect_failures = [var.volume_size]
}
run "shared_retention_identity" {
  command = plan
  variables {
    node_principal      = "arn:aws:iam:::user/p123456:SAMEKEY"
    retention_principal = "arn:aws:iam:::user/p123456:SAMEKEY"
  }
  expect_failures = [var.retention_principal]
}
