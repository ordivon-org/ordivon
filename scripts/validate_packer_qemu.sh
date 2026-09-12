#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/providers/packer"
packer init .
packer validate -syntax-only .
packer plugins installed | grep -F 'github.com/hashicorp/qemu/'
echo 'packerQemuProvider=AVAILABLE_SYNTAX_VALID'
