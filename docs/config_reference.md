# Configuration Reference

This document describes all configuration options available for the iHeart Recorder project.

---

## audio_processing_config.json
- **enabled**: (bool) Enable or disable audio processing globally.
- **enable_noise_reduction**: (bool) Enable noise reduction processing.
- **noise_reduction_strength**: (float, 0.0-1.0) Controls the aggressiveness of noise reduction.
- **preserve_original**: (bool) If true, original audio files are preserved after processing.
- **output_suffix**: (str) Suffix appended to processed files (e.g., `_processed`).

## default_config.ini
- [Add documentation for .ini options here if used]

## Environment Variables
- **CLIENT_SECRETS_PATH**: Path to Google API client secrets (used for automation/login).
- **IHEART_USERNAME**: Username for automation (do not hardcode in code).
- **IHEART_PASSWORD**: Password for automation (do not hardcode in code).

---

For more information, see comments in `config.py` or the main README.
