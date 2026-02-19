#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMTOOL_CONFIG_FILE="${PROMTOOL_CONFIG_FILE:-${ROOT_DIR}/config/promtool-installer.defaults}"
PROMTOOL_VALIDATE_REMOTE="${PROMTOOL_VALIDATE_REMOTE:-0}"

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

normalized_validate_remote="$(echo "${PROMTOOL_VALIDATE_REMOTE}" | tr '[:upper:]' '[:lower:]')"
if [[ "${normalized_validate_remote}" == "1" || "${normalized_validate_remote}" == "true" || "${normalized_validate_remote}" == "yes" || "${normalized_validate_remote}" == "on" ]]; then
  PROMTOOL_SHA256SUMS_URL="${PROMTOOL_SHA256SUMS_URL:-https://github.com/prometheus/prometheus/releases/download/v${PROMTOOL_DEFAULT_VERSION}/sha256sums.txt}"
  archive_amd64="prometheus-${PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz"
  archive_arm64="prometheus-${PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz"

  sha256sums_file="$(mktemp)"
  cleanup() {
    rm -f "${sha256sums_file}"
  }
  trap cleanup EXIT

  if ! curl -fsSL -o "${sha256sums_file}" "${PROMTOOL_SHA256SUMS_URL}"; then
    echo "[validate-promtool-installer-config] failed to fetch sha256sums: ${PROMTOOL_SHA256SUMS_URL}" >&2
    exit 1
  fi

  remote_amd64="$(awk -v file_name="${archive_amd64}" '$2==file_name {print $1; exit}' "${sha256sums_file}")"
  remote_arm64="$(awk -v file_name="${archive_arm64}" '$2==file_name {print $1; exit}' "${sha256sums_file}")"

  if [[ -z "${remote_amd64}" ]]; then
    echo "[validate-promtool-installer-config] checksum entry not found for ${archive_amd64}" >&2
    exit 1
  fi
  if [[ -z "${remote_arm64}" ]]; then
    echo "[validate-promtool-installer-config] checksum entry not found for ${archive_arm64}" >&2
    exit 1
  fi
  if [[ "${remote_amd64}" != "${PROMTOOL_DEFAULT_SHA256_LINUX_AMD64}" ]]; then
    echo "[validate-promtool-installer-config] checksum mismatch for ${archive_amd64}" >&2
    exit 1
  fi
  if [[ "${remote_arm64}" != "${PROMTOOL_DEFAULT_SHA256_LINUX_ARM64}" ]]; then
    echo "[validate-promtool-installer-config] checksum mismatch for ${archive_arm64}" >&2
    exit 1
  fi

  echo "[validate-promtool-installer-config] remote checksum validation passed: ${PROMTOOL_SHA256SUMS_URL}" >&2
fi

echo "[validate-promtool-installer-config] config is valid: ${PROMTOOL_CONFIG_FILE}" >&2
