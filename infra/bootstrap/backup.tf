resource "aws_s3_bucket" "state" {
  bucket        = var.bucket_name
  force_destroy = false
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect       = "Deny"
        NotPrincipal = { AWS = [var.state_principal, var.retention_principal, var.owner_principal] }
        Action       = "s3:*"
        Resource     = ["arn:aws:s3:::${var.bucket_name}", "arn:aws:s3:::${var.bucket_name}/*"]
      },
      {
        Effect    = "Deny"
        Principal = { AWS = var.state_principal }
        Action    = ["s3:DeleteObject", "s3:DeleteObjectVersion", "s3:DeleteBucket", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy", "s3:PutLifecycleConfiguration", "s3:PutBucketAcl", "s3:PutObjectAcl"]
        Resource  = ["arn:aws:s3:::${var.bucket_name}", "arn:aws:s3:::${var.bucket_name}/*"]
      },
      {
        Effect    = "Allow"
        Principal = { AWS = [var.state_principal, var.retention_principal] }
        Action    = ["s3:ListBucket", "s3:GetBucketLocation"]
        Resource  = "arn:aws:s3:::${var.bucket_name}"
      },
      {
        Effect    = "Allow"
        Principal = { AWS = var.state_principal }
        Action    = ["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
        Resource  = "arn:aws:s3:::${var.bucket_name}/state/epoch-1/*"
      },
      {
        Effect    = "Allow"
        Principal = { AWS = var.retention_principal }
        Action    = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
        Resource  = "arn:aws:s3:::${var.bucket_name}/state/epoch-1/*"
      }
    ]
  })
  lifecycle {
    prevent_destroy = true
  }
}
