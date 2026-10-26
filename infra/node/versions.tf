terraform {
  required_version = "= 1.13.5"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "= 1.70.2"
    }
  }
  backend "pg" {}
}

provider "hcloud" {}
