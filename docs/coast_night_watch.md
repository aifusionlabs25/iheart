# Coast Night Watch

The night-watch path is designed to record Coast to Coast through a dedicated browser/audio route without changing the normal Windows speaker output.

## Audio Routing Goal

- Leave Windows default output on the normal speakers.
- Use Microsoft Edge only for the iHeart/Coast stream.
- Route Edge output to `Sceptre F27 (NVIDIA High Definition Audio)` in Windows Volume Mixer.
- Prefer the Sceptre WASAPI loopback device when Windows exposes it:

```text
Device 16: Sceptre F27 (NVIDIA High Definition Audio) [Loopback]
```

- If the Sceptre/NVIDIA route is not exposed, the wrapper falls back to the verified Realtek WASAPI loopback route.

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

The preflight prints the capture device it selected. It prefers Sceptre/NVIDIA when available and otherwise uses the Realtek WASAPI fallback that was verified during the 2026-05-17 overnight recovery.

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

## Compression

Recordings are compressed to MP3 after the WAV is written. The app auto-discovers FFmpeg from a local bundle, system PATH, or the common WinGet FFmpeg install.

The original WAV is kept after compression so the wrapper can still run post-recording verification. Delete WAV files only after the MP3 and verification result are confirmed.

## Nightly Report

The nightly report should include:

- scheduled task start status
- recording completion status
- newest WAV path when present
- newest MP3 path when present
- WAV and MP3 file sizes
- duration
- RMS
- transcript or recording warnings
- compression success or failure
- whether any iHeart popup or ad overlay blocked playback

Compression failure should be reported clearly, but it should not hide the recording verification result.

## Warning Noise

Known harmless recording warnings may be filtered only when they are understood and documented.

Keep real failures visible, including:

- missing output file
- very short recording
- silent or near-silent RMS
- failed FFmpeg compression
- browser or playback launch failure
- ad or popup overlay blocking audio

## Retention Policy

Default retention rule:

- Keep WAV files until the matching MP3 and verification result are confirmed.
- Keep MP3 files as the long-term listening copy.
- Do not delete unverified recordings automatically.
- Do not bulk-delete recordings without Rob approval.
- Prefer a dry-run cleanup report before any deletion.

## Production Schedule

The Windows Scheduled Task is:

```text
\AI Fusion Labs\Coast Night Watch
```

Production timing:

- start: `11:05 PM` Arizona time
- duration: `14400` seconds / 4 hours
- expected coverage: about `11:05 PM` to `3:05 AM`

That start time avoids most of the pre-show news feed and still gives the browser a few minutes to load, clear popups, and start playback before the show usually begins around `11:10 PM`.

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
- If the Sceptre/NVIDIA route disappears, verify a short Realtek fallback recording before relying on the overnight run.
