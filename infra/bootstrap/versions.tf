terraform {
  required_version = "= 1.13.5"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "= 1.70.2"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.70.0"
    }
  }
}
provider "hcloud" {}
provider "aws" {
  region                      = var.backup_location
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  s3_use_path_style           = true
  endpoints {
    s3 = "https://${var.backup_location}.your-objectstorage.com"
  }
}
