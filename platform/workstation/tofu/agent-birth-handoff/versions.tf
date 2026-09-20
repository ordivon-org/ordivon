terraform {
  required_version = "= 1.12.6"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "= 5.25.0"
    }
  }

  backend "local" {
    path = "/var/lib/ordivon/operations-v2/tofu/agent-birth-handoff/terraform.tfstate"
  }
}

provider "cloudflare" {}
