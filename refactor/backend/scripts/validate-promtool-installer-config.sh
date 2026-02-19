#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMTOOL_CONFIG_FILE="${PROMTOOL_CONFIG_FILE:-${ROOT_DIR}/config/promtool-installer.defaults}"
PROMTOOL_VALIDATE_REMOTE="${PROMTOOL_VALIDATE_REMOTE:-0}"
PROMTOOL_VALIDATE_REMOTE_MODE="${PROMTOOL_VALIDATE_REMOTE_MODE:-strict}"
PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS="${PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS:-3}"
PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS="${PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS:-10}"
PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS="${PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS:-30}"
PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS="${PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS:-1}"
PROMTOOL_REMOTE_FETCH_CACHE_FILE="${PROMTOOL_REMOTE_FETCH_CACHE_FILE:-}"
PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS="${PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS:-3600}"

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

validate_positive_integer() {
  local key_name="$1"
  local key_value="$2"

  if [[ ! "${key_value}" =~ ^[0-9]+$ ]] || (( key_value < 1 )); then
    echo "[validate-promtool-installer-config] ${key_name} must be a positive integer: ${key_value}" >&2
    exit 1
  fi
}

validate_non_negative_integer() {
  local key_name="$1"
  local key_value="$2"

  if [[ ! "${key_value}" =~ ^[0-9]+$ ]]; then
    echo "[validate-promtool-installer-config] ${key_name} must be a non-negative integer: ${key_value}" >&2
    exit 1
  fi
}

run_remote_checksum_validation() {
  local archive_amd64="prometheus-${PROMTOOL_DEFAULT_VERSION}.linux-amd64.tar.gz"
  local archive_arm64="prometheus-${PROMTOOL_DEFAULT_VERSION}.linux-arm64.tar.gz"
  local sha256sums_file
  local fetch_succeeded=0
  local attempt=1
  local now_epoch
  local cache_age
  local cached_at_raw
  local cache_meta_file=""
  local cache_dir=""
  local remote_amd64
  local remote_arm64

  PROMTOOL_SHA256SUMS_URL="${PROMTOOL_SHA256SUMS_URL:-https://github.com/prometheus/prometheus/releases/download/v${PROMTOOL_DEFAULT_VERSION}/sha256sums.txt}"
  sha256sums_file="$(mktemp)"

  if [[ -n "${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" ]]; then
    cache_meta_file="${PROMTOOL_REMOTE_FETCH_CACHE_FILE}.meta"
    if [[ -f "${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" && -f "${cache_meta_file}" ]]; then
      cached_at_raw="$(tr -d '[:space:]' < "${cache_meta_file}" || true)"
      if [[ "${cached_at_raw}" =~ ^[0-9]+$ ]]; then
        now_epoch="$(date +%s)"
        cache_age=$((now_epoch - cached_at_raw))
        if (( cache_age >= 0 && cache_age <= PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS )); then
          cp "${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" "${sha256sums_file}"
          fetch_succeeded=1
          echo "[validate-promtool-installer-config] using cached sha256sums metadata: ${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" >&2
        else
          echo "[validate-promtool-installer-config] cached sha256sums metadata is stale (age ${cache_age}s > ttl ${PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS}s): ${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" >&2
        fi
      else
        echo "[validate-promtool-installer-config] cached sha256sums metadata timestamp is invalid: ${cache_meta_file}" >&2
      fi
    fi
  fi

  if (( fetch_succeeded != 1 )); then
    while (( attempt <= PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS )); do
      if curl -fsSL \
        --connect-timeout "${PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS}" \
        --max-time "${PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS}" \
        -o "${sha256sums_file}" \
        "${PROMTOOL_SHA256SUMS_URL}"; then
        fetch_succeeded=1
        break
      fi

      if (( attempt < PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS )); then
        echo "[validate-promtool-installer-config] failed to fetch sha256sums (attempt ${attempt}/${PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS}), retry in ${PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS}s: ${PROMTOOL_SHA256SUMS_URL}" >&2
        sleep "${PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS}"
      fi

      attempt=$((attempt + 1))
    done

    if (( fetch_succeeded != 1 )); then
      rm -f "${sha256sums_file}"
      echo "[validate-promtool-installer-config] failed to fetch sha256sums after ${PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS} attempt(s): ${PROMTOOL_SHA256SUMS_URL}" >&2
      return 1
    fi

    if [[ -n "${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" ]]; then
      cache_dir="$(dirname "${PROMTOOL_REMOTE_FETCH_CACHE_FILE}")"
      cache_meta_file="${PROMTOOL_REMOTE_FETCH_CACHE_FILE}.meta"
      if ! mkdir -p "${cache_dir}" \
        || ! cp "${sha256sums_file}" "${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" \
        || ! printf "%s\n" "$(date +%s)" > "${cache_meta_file}"; then
        echo "[validate-promtool-installer-config] warning: failed to update sha256sums cache: ${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" >&2
      else
        echo "[validate-promtool-installer-config] updated sha256sums cache: ${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" >&2
      fi
    fi
  fi

  remote_amd64="$(awk -v file_name="${archive_amd64}" '$2==file_name {print $1; exit}' "${sha256sums_file}")"
  remote_arm64="$(awk -v file_name="${archive_arm64}" '$2==file_name {print $1; exit}' "${sha256sums_file}")"

  if [[ -z "${remote_amd64}" ]]; then
    rm -f "${sha256sums_file}"
    echo "[validate-promtool-installer-config] checksum entry not found for ${archive_amd64}" >&2
    return 1
  fi
  if [[ -z "${remote_arm64}" ]]; then
    rm -f "${sha256sums_file}"
    echo "[validate-promtool-installer-config] checksum entry not found for ${archive_arm64}" >&2
    return 1
  fi
  if [[ "${remote_amd64}" != "${PROMTOOL_DEFAULT_SHA256_LINUX_AMD64}" ]]; then
    rm -f "${sha256sums_file}"
    echo "[validate-promtool-installer-config] checksum mismatch for ${archive_amd64}" >&2
    return 1
  fi
  if [[ "${remote_arm64}" != "${PROMTOOL_DEFAULT_SHA256_LINUX_ARM64}" ]]; then
    rm -f "${sha256sums_file}"
    echo "[validate-promtool-installer-config] checksum mismatch for ${archive_arm64}" >&2
    return 1
  fi

  rm -f "${sha256sums_file}"
  echo "[validate-promtool-installer-config] remote checksum validation passed: ${PROMTOOL_SHA256SUMS_URL}" >&2
  return 0
}

normalized_validate_remote="$(echo "${PROMTOOL_VALIDATE_REMOTE}" | tr '[:upper:]' '[:lower:]')"
if [[ "${normalized_validate_remote}" == "1" || "${normalized_validate_remote}" == "true" || "${normalized_validate_remote}" == "yes" || "${normalized_validate_remote}" == "on" ]]; then
  normalized_validate_remote_mode="$(echo "${PROMTOOL_VALIDATE_REMOTE_MODE}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${normalized_validate_remote_mode}" != "strict" && "${normalized_validate_remote_mode}" != "soft" ]]; then
    echo "[validate-promtool-installer-config] PROMTOOL_VALIDATE_REMOTE_MODE must be one of: strict, soft (got: ${PROMTOOL_VALIDATE_REMOTE_MODE})" >&2
    exit 1
  fi
  validate_positive_integer "PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS" "${PROMTOOL_REMOTE_FETCH_MAX_ATTEMPTS}"
  validate_positive_integer "PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS" "${PROMTOOL_REMOTE_FETCH_CONNECT_TIMEOUT_SECONDS}"
  validate_positive_integer "PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS" "${PROMTOOL_REMOTE_FETCH_TIMEOUT_SECONDS}"
  validate_non_negative_integer "PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS" "${PROMTOOL_REMOTE_FETCH_RETRY_DELAY_SECONDS}"
  if [[ -n "${PROMTOOL_REMOTE_FETCH_CACHE_FILE}" ]]; then
    validate_positive_integer "PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS" "${PROMTOOL_REMOTE_FETCH_CACHE_TTL_SECONDS}"
  fi

  if ! run_remote_checksum_validation; then
    if [[ "${normalized_validate_remote_mode}" == "soft" ]]; then
      echo "[validate-promtool-installer-config] remote checksum validation failed in soft mode, continue." >&2
    else
      exit 1
    fi
  fi
fi

echo "[validate-promtool-installer-config] config is valid: ${PROMTOOL_CONFIG_FILE}" >&2
