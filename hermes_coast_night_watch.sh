#!/usr/bin/env bash
set -euo pipefail

DURATION_SECONDS="${1:-900}"
DEVICE_INDEX="${COAST_DEVICE_INDEX:-16}"
ROOT_WIN='C:\AI Fusion Labs\AI folder from OG Comp\iheart_dev'
POWERSHELL='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'

"$POWERSHELL" -NoProfile -ExecutionPolicy Bypass \
  -File "$ROOT_WIN\\coast_night_watch.ps1" \
  -DurationSeconds "$DURATION_SECONDS" \
  -DeviceIndex "$DEVICE_INDEX" \
  -ConfirmBrowserRoutedToMonitor
