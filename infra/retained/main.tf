locals {
  name       = "${var.tenant}-${var.environment}"
  bucket_arn = "arn:aws:s3:::${var.bucket_name}"
  repo_path  = "${var.tenant}/${var.environment}/epoch-1"
}
resource "hcloud_volume" "postgres" {
  name              = "${local.name}-postgres"
  size              = var.volume_size
  location          = var.location
  delete_protection = true
  labels            = { tenant = var.tenant, environment = var.environment, managed_by = "bato" }
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_s3_bucket" "backup" {
  bucket        = var.bucket_name
  force_destroy = false
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_s3_bucket_policy" "backup" {
  bucket = aws_s3_bucket.backup.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid          = "OnlyNamedKeys"
        Effect       = "Deny"
        NotPrincipal = { AWS = [var.node_principal, var.retention_principal, var.owner_principal, var.plan_principal] }
        Action       = "s3:*"
        Resource     = [local.bucket_arn, "${local.bucket_arn}/*"]
      },
      {
        Sid       = "NodeCannotDeleteOrChangePolicy"
        Effect    = "Deny"
        Principal = { AWS = var.node_principal }
        Action    = ["s3:DeleteObject", "s3:DeleteObjectVersion", "s3:DeleteBucket", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy", "s3:PutLifecycleConfiguration", "s3:PutBucketAcl", "s3:PutObjectAcl"]
        Resource  = [local.bucket_arn, "${local.bucket_arn}/*"]
      },
      {
        Sid       = "NodeListOwnRepository"
        Effect    = "Allow"
        Principal = { AWS = var.node_principal }
        Action    = ["s3:ListBucket"]
        Resource  = local.bucket_arn
        Condition = { StringLike = { "s3:prefix" = ["${local.repo_path}", "${local.repo_path}/*"] } }
      },
      {
        Sid       = "NodeReadWriteOwnRepository"
        Effect    = "Allow"
        Principal = { AWS = var.node_principal }
        Action    = ["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
        Resource  = "${local.bucket_arn}/${local.repo_path}/*"
      },
      {
        Sid         = "NodeOutsideRepository"
        Effect      = "Deny"
        Principal   = { AWS = var.node_principal }
        Action      = ["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
        NotResource = "${local.bucket_arn}/${local.repo_path}/*"
      },
      {
        Sid       = "OffNodeRetention"
        Effect    = "Allow"
        Principal = { AWS = var.retention_principal }
        Action    = ["s3:ListBucket", "s3:GetBucketLocation"]
        Resource  = local.bucket_arn
      },
      {
        Sid       = "OffNodeExpireOwnRepository"
        Effect    = "Allow"
        Principal = { AWS = var.retention_principal }
        Action    = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
        Resource  = "${local.bucket_arn}/${local.repo_path}/*"
      },
      {
        Sid       = "ReadOnlyPlans"
        Effect    = "Allow"
        Principal = { AWS = var.plan_principal }
        Action = [
          "s3:ListBucket", "s3:GetBucketLocation", "s3:GetBucketPolicy", "s3:GetBucketAcl",
          "s3:GetBucketCORS", "s3:GetBucketWebsite", "s3:GetBucketVersioning",
          "s3:GetAccelerateConfiguration", "s3:GetBucketRequestPayment", "s3:GetBucketLogging",
          "s3:GetLifecycleConfiguration", "s3:GetReplicationConfiguration",
          "s3:GetEncryptionConfiguration", "s3:GetBucketObjectLockConfiguration", "s3:GetBucketTagging"
        ]
        Resource = local.bucket_arn
      },
      {
        Sid       = "PlansCannotReadDataOrMutate"
        Effect    = "Deny"
        Principal = { AWS = var.plan_principal }
        Action = [
          "s3:GetObject*", "s3:Put*", "s3:Delete*", "s3:CreateBucket",
          "s3:AbortMultipartUpload", "s3:RestoreObject", "s3:Replicate*",
          "s3:BypassGovernanceRetention"
        ]
        Resource = [local.bucket_arn, "${local.bucket_arn}/*"]
      }
    ]
  })
  lifecycle {
    prevent_destroy = true
  }
}
output "volume_id" {
  value = hcloud_volume.postgres.id
}
output "volume_name" {
  value = hcloud_volume.postgres.name
}
output "repository" {
  value = { bucket = var.bucket_name, endpoint = "${var.backup_location}.your-objectstorage.com", region = var.backup_location, path = "/${local.repo_path}" }
}
