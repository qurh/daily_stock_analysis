#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMTOOL_CONFIG_FILE="${PROMTOOL_CONFIG_FILE:-${ROOT_DIR}/config/promtool-installer.defaults}"

if [[ ! -f "${PROMTOOL_CONFIG_FILE}" ]]; then
  echo "[validate-promtool-installer-config] config file not found: ${PROMTOOL_CONFIG_FILE}" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${PROMTOOL_CONFIG_FILE}"

required_vars=(
  "PROMTOOL_DEFAULT_VERSION"
  "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64"
  "PROMTOOL_DEFAULT_SHA256_LINUX_ARM64"
)

for required_var in "${required_vars[@]}"; do
  if [[ -z "${!required_var:-}" ]]; then
    echo "[validate-promtool-installer-config] missing required key: ${required_var}" >&2
    exit 1
  fi
done

if [[ ! "${PROMTOOL_DEFAULT_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "[validate-promtool-installer-config] PROMTOOL_DEFAULT_VERSION must match X.Y.Z: ${PROMTOOL_DEFAULT_VERSION}" >&2
  exit 1
fi

validate_checksum() {
  local key_name="$1"
  local key_value="$2"

  if [[ ! "${key_value}" =~ ^[0-9a-f]{64}$ ]]; then
    echo "[validate-promtool-installer-config] ${key_name} must be a 64-character lowercase hex string: ${key_value}" >&2
    exit 1
  fi
}

validate_checksum "PROMTOOL_DEFAULT_SHA256_LINUX_AMD64" "${PROMTOOL_DEFAULT_SHA256_LINUX_AMD64}"
validate_checksum "PROMTOOL_DEFAULT_SHA256_LINUX_ARM64" "${PROMTOOL_DEFAULT_SHA256_LINUX_ARM64}"

echo "[validate-promtool-installer-config] config is valid: ${PROMTOOL_CONFIG_FILE}" >&2
