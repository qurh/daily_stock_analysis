#!/usr/bin/env bash
set -euo pipefail

PROMTOOL_VERSION="${PROMTOOL_VERSION:-2.52.0}"
PROMTOOL_PLATFORM="${PROMTOOL_PLATFORM:-}"
PROMTOOL_TMP_DIR="${PROMTOOL_TMP_DIR:-/tmp}"
PROMTOOL_INSTALL_DIR="${PROMTOOL_INSTALL_DIR:-/usr/local/bin}"
PROMTOOL_DRY_RUN="${PROMTOOL_DRY_RUN:-0}"
PROMTOOL_MACHINE_ARCH="${PROMTOOL_MACHINE_ARCH:-}"

if [[ -z "${PROMTOOL_PLATFORM}" ]]; then
  machine_arch="${PROMTOOL_MACHINE_ARCH:-$(uname -m)}"
  case "${machine_arch}" in
    x86_64 | amd64)
      PROMTOOL_PLATFORM="linux-amd64"
      ;;
    aarch64 | arm64)
      PROMTOOL_PLATFORM="linux-arm64"
      ;;
    *)
      echo "[install-promtool] unsupported machine architecture: ${machine_arch}" >&2
      exit 1
      ;;
  esac
fi

if [[ -z "${PROMTOOL_SHA256:-}" ]]; then
  case "${PROMTOOL_PLATFORM}" in
    linux-amd64)
      PROMTOOL_SHA256="7f31c5d6474bbff3e514e627e0b7a7fbbd4e5cea3f315fd0b76cad50be4c1ba3"
      ;;
    linux-arm64)
      PROMTOOL_SHA256="b503c0f552e381d7d3f84dfd275166bf07c74f99c428ffed69447d4ab3259901"
      ;;
    *)
      echo "[install-promtool] missing PROMTOOL_SHA256 for platform: ${PROMTOOL_PLATFORM}" >&2
      exit 1
      ;;
  esac
fi

archive="prometheus-${PROMTOOL_VERSION}.${PROMTOOL_PLATFORM}.tar.gz"
download_url="https://github.com/prometheus/prometheus/releases/download/v${PROMTOOL_VERSION}/${archive}"
archive_path="${PROMTOOL_TMP_DIR}/${archive}"
extract_dir="${PROMTOOL_TMP_DIR}/prometheus-${PROMTOOL_VERSION}.${PROMTOOL_PLATFORM}"
binary_path="${extract_dir}/promtool"
target_path="${PROMTOOL_INSTALL_DIR}/promtool"

echo "[install-promtool] platform: ${PROMTOOL_PLATFORM}" >&2
if [[ "${PROMTOOL_DRY_RUN}" == "1" ]]; then
  echo "[install-promtool] dry run enabled; skip download/install." >&2
  exit 0
fi

echo "[install-promtool] downloading ${download_url}" >&2
curl -fsSL -o "${archive_path}" "${download_url}"

echo "[install-promtool] verifying sha256 checksum" >&2
echo "${PROMTOOL_SHA256}  ${archive_path}" | sha256sum -c -

echo "[install-promtool] extracting ${archive_path}" >&2
tar -xzf "${archive_path}" -C "${PROMTOOL_TMP_DIR}"

echo "[install-promtool] installing binary to ${target_path}" >&2
if [[ -w "${PROMTOOL_INSTALL_DIR}" ]]; then
  install "${binary_path}" "${target_path}"
elif command -v sudo >/dev/null 2>&1; then
  sudo install "${binary_path}" "${target_path}"
else
  echo "[install-promtool] install directory is not writable and sudo is unavailable: ${PROMTOOL_INSTALL_DIR}" >&2
  exit 1
fi

"${target_path}" --version
