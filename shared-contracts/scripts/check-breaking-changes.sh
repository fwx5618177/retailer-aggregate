#!/usr/bin/env bash
#
# check-breaking-changes.sh
#
# Detects breaking changes in the OpenAPI spec by comparing the current
# working-tree version against the version on a base branch (default: main).
#
# Usage:
#   ./scripts/check-breaking-changes.sh [base-branch]
#
# Examples:
#   ./scripts/check-breaking-changes.sh            # compare against main
#   ./scripts/check-breaking-changes.sh develop     # compare against develop
#   ./scripts/check-breaking-changes.sh HEAD~3      # compare against 3 commits ago
#
# Prerequisites:
#   - oasdiff must be installed (https://github.com/Tufin/oasdiff)
#     Install via: go install github.com/Tufin/oasdiff@latest
#                  or: brew install tufin/oasdiff/oasdiff
#
# Exit codes:
#   0 - No breaking changes detected
#   1 - Breaking changes detected or an error occurred
#

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_BRANCH="${1:-main}"
SPEC_PATH="shared-contracts/openapi/api-v1.yaml"

# Resolve the repo root (this script lives in shared-contracts/scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

CURRENT_SPEC="${REPO_ROOT}/${SPEC_PATH}"
TEMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${TEMP_DIR}"
}
trap cleanup EXIT

# ── Preflight checks ──────────────────────────────────────────────────────────
if ! command -v oasdiff &>/dev/null; then
  echo "ERROR: oasdiff is not installed."
  echo ""
  echo "Install it with one of:"
  echo "  go install github.com/Tufin/oasdiff@latest"
  echo "  brew install tufin/oasdiff/oasdiff"
  echo "  curl -fsSL https://github.com/Tufin/oasdiff/releases/latest/download/oasdiff_<version>_<os>_<arch>.tar.gz | tar -xz"
  echo ""
  echo "See https://github.com/Tufin/oasdiff for details."
  exit 1
fi

if [ ! -f "${CURRENT_SPEC}" ]; then
  echo "ERROR: Current spec not found at ${CURRENT_SPEC}"
  exit 1
fi

# ── Extract base branch spec ──────────────────────────────────────────────────
echo "Comparing OpenAPI spec against base: ${BASE_BRANCH}"
echo "  Spec path: ${SPEC_PATH}"
echo ""

BASE_SPEC="${TEMP_DIR}/api-v1-base.yaml"

if ! git -C "${REPO_ROOT}" show "${BASE_BRANCH}:${SPEC_PATH}" > "${BASE_SPEC}" 2>/dev/null; then
  echo "WARNING: Could not find ${SPEC_PATH} on branch '${BASE_BRANCH}'."
  echo "This is expected if the spec is brand new."
  echo "No breaking change comparison possible -- exiting cleanly."
  exit 0
fi

# ── Breaking change detection ─────────────────────────────────────────────────
echo "──────────────────────────────────────────────"
echo "  Breaking Change Report"
echo "──────────────────────────────────────────────"
echo ""

BREAKING_EXIT=0
oasdiff breaking "${BASE_SPEC}" "${CURRENT_SPEC}" --fail-on ERR || BREAKING_EXIT=$?

echo ""

if [ "${BREAKING_EXIT}" -ne 0 ]; then
  echo "RESULT: Breaking changes detected!"
  echo ""
  echo "If these changes are intentional, coordinate with all API consumers"
  echo "and bump the API version before merging."
else
  echo "RESULT: No breaking changes detected."
fi

# ── Full changelog (informational) ────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
echo "  Full Changelog"
echo "──────────────────────────────────────────────"
echo ""

oasdiff changelog "${BASE_SPEC}" "${CURRENT_SPEC}" || true

echo ""
echo "──────────────────────────────────────────────"

exit "${BREAKING_EXIT}"
