# PolicyGraph Baseline Test - Terraform Provider Configuration
# Generated for tfsec scanning

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  # These are placeholder values for static analysis only
  # tfsec does not require actual AWS credentials
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}
