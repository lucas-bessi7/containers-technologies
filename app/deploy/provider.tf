terraform {
  backend "s3" {}
}
provider "aws" {
  default_tags {
    tags = {
      Project = "lab03"
      Owner   = "lucas-bessi7"
    }
  }
}
