# Coast Night Watch

The night-watch path is designed to record Coast to Coast through a dedicated browser/audio route without changing the normal Windows speaker output.

## Audio Routing Goal

- Leave Windows default output on the normal speakers.
- Use Microsoft Edge only for the iHeart/Coast stream.
- Route Edge output to `Sceptre F27 (NVIDIA High Definition Audio)` in Windows Volume Mixer.
- Capture the Sceptre WASAPI loopback device:

```text
Device 16: Sceptre F27 (NVIDIA High Definition Audio) [Loopback]
```

## First-Time Manual Setup

1. Start a short Edge/iHeart test only when the house can tolerate a mistake.
2. Open Windows Settings.
3. Go to System > Sound > Volume mixer.
4. Find Microsoft Edge.
5. Set Edge output to `Sceptre F27 / NVIDIA High Definition Audio`.
6. Leave Chrome and the Windows default output unchanged.

Windows should remember the per-app routing for Edge after it is set.

## Preflight

This command checks devices and exits before launching a browser or recording:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\coast_night_watch.ps1 -PreflightOnly
```

Once Edge is routed to the Sceptre output, confirm the route explicitly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\coast_night_watch.ps1 -PreflightOnly -ConfirmBrowserRoutedToMonitor
```

## Short Recording Test

Run a 5-minute test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\coast_night_watch.ps1 -DurationSeconds 300 -ConfirmBrowserRoutedToMonitor
```

The wrapper verifies the newest `Rec_*.wav` after the mission. It fails if the file is too short or the RMS signal level looks silent.

## Final Test Candidate

Run a 15-minute final test before trusting an overnight run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\coast_night_watch.ps1 -DurationSeconds 900 -ConfirmBrowserRoutedToMonitor
```

Expected verification:

- duration at least 90% of the requested duration
- stereo or mono WAV with a valid sample rate
- RMS above `100`

## Hermes / WSL Command

Hermes runs inside WSL, so use the included Bash wrapper:

```bash
cd "/mnt/c/AI Fusion Labs/AI folder from OG Comp/iheart_dev"
./hermes_coast_night_watch.sh 900
```

That launches the same Windows PowerShell wrapper, keeps Edge as the dedicated browser, and runs the same post-recording verification.

## Safety

- Do not use this for a full overnight run until a short recording test verifies audio is captured.
- Do not change the Windows default speaker output for this workflow.
- Do not schedule this until the Edge routing and file verification are proven.
