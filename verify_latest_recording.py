import argparse
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import audioop
import sys
import wave
from pathlib import Path


def latest_recording(root):
    files = sorted(Path(root).glob("Rec_*.wav"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No Rec_*.wav files found in {root}")
    return files[0]


def inspect_wav(path):
    with wave.open(str(path), "rb") as wav:
        frames = wav.readframes(wav.getnframes())
        duration = wav.getnframes() / wav.getframerate() if wav.getframerate() else 0
        rms = audioop.rms(frames, wav.getsampwidth()) if frames else 0
        return {
            "path": path,
            "bytes": path.stat().st_size,
            "duration": duration,
            "channels": wav.getnchannels(),
            "rate": wav.getframerate(),
            "rms": rms,
        }


def main():
    parser = argparse.ArgumentParser(description="Verify the newest Coast night-watch WAV recording.")
    parser.add_argument("--root", default=".", help="Directory containing Rec_*.wav files.")
    parser.add_argument("--min-duration", type=float, default=30.0, help="Minimum acceptable WAV duration in seconds.")
    parser.add_argument("--min-rms", type=int, default=100, help="Minimum acceptable RMS signal level.")
    args = parser.parse_args()

    try:
        info = inspect_wav(latest_recording(args.root))
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}", file=sys.stderr)
        return 1

    print("Latest recording verification")
    print(f"File:     {info['path']}")
    print(f"Bytes:    {info['bytes']}")
    print(f"Duration: {info['duration']:.2f}s")
    print(f"Channels: {info['channels']}")
    print(f"Rate:     {info['rate']} Hz")
    print(f"RMS:      {info['rms']}")

    failures = []
    if info["duration"] < args.min_duration:
        failures.append(f"duration {info['duration']:.2f}s is below {args.min_duration:.2f}s")
    if info["rms"] < args.min_rms:
        failures.append(f"RMS {info['rms']} is below {args.min_rms}")
    if info["channels"] < 1:
        failures.append("recording has no channels")
    if info["rate"] <= 0:
        failures.append("recording has invalid sample rate")

    if failures:
        print("VERIFY FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("VERIFY PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
