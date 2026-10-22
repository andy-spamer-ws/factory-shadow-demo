#!/usr/bin/env bash
# Prints a simulated test run for one stage and writes a line to the job summary.
# Usage: simulate-tests.sh <stage> <label> <check-count> <seconds>
# Fails the stage's last check when FAIL_STAGE equals <stage>.
set -euo pipefail

stage="$1"
label="$2"
count="$3"
duration="$4"
fail_stage="${FAIL_STAGE:-none}"
delay=$(awk -v d="$duration" -v c="$count" 'BEGIN { printf "%.2f", d / c }')

passed=0
failed=0
echo "::group::${label} (${count} checks)"
for i in $(seq 1 "$count"); do
  name="test_${stage}_$(printf '%03d' "$i")"
  if [[ "$fail_stage" == "$stage" && "$i" -eq "$count" ]]; then
    echo "FAIL  ${name}"
    echo "::error title=${label} failed::${name} failed (simulated, fail_stage=${fail_stage})"
    failed=$((failed + 1))
  else
    echo "PASS  ${name}"
    passed=$((passed + 1))
  fi
  sleep "$delay"
done
echo "::endgroup::"

status=$([[ "$failed" -eq 0 ]] && echo "✅ passed" || echo "❌ failed")
{
  echo "| Stage | Result | Passed | Failed |"
  echo "| --- | --- | --- | --- |"
  echo "| ${label} | ${status} | ${passed} | ${failed} |"
} >> "${GITHUB_STEP_SUMMARY:-/dev/null}"

echo "${label}: ${passed} passed, ${failed} failed"
[[ "$failed" -eq 0 ]]
