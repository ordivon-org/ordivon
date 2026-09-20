variable "iso_url" {
  type        = string
  description = "Caller-supplied authoritative installation image URI."
}

variable "iso_checksum" {
  type        = string
  description = "Caller-supplied digest for the exact authoritative installation image, e.g. sha256:<hex>."

  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.iso_checksum))
    error_message = "ISO checksum must be an exact lowercase SHA-256 digest."
  }
}

source "qemu" "security_v2_validation" {
  accelerator      = "kvm"
  communicator     = "none"
  disk_size        = "64M"
  format           = "qcow2"
  headless         = true
  iso_checksum     = var.iso_checksum
  iso_url          = var.iso_url
  output_directory = "/tmp/security-v2-packer-validation-output"
}

build {
  sources = ["source.qemu.security_v2_validation"]
}
