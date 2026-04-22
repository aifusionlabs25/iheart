# MP3 Compression Guide

## Overview

The iHeart Recorder now includes automatic MP3 compression to significantly reduce file sizes. This feature uses FFmpeg to compress WAV recordings to MP3 format after recording completes.

## File Size Reduction

### Before Compression
- **4-hour recording**: ~3.8 GB (uncompressed WAV)
- **Format**: 44.1kHz, 16-bit, Stereo, PCM

### After Compression (192kbps MP3)
- **4-hour recording**: ~330 MB (MP3)
- **Reduction**: ~90% smaller files
- **Quality**: Excellent for radio/voice content

### Bitrate Options

| Bitrate | Quality | File Size (4-hour) | Use Case |
|---------|---------|-------------------|----------|
| 128k | Good | ~220 MB | Maximum compression |
| 192k | Very Good | ~330 MB | **Recommended** for radio |
| 256k | Excellent | ~440 MB | High quality music |
| 320k | Best | ~550 MB | Maximum quality |

## Configuration

### Default Settings (in `config.py`)
```python
ENABLE_COMPRESSION = True      # Enable automatic compression
MP3_BITRATE = "192k"          # MP3 bitrate
DELETE_ORIGINAL_WAV = False   # Keep original WAV files
```

### GUI Settings

1. Open the **Settings** tab in the GUI
2. Find the **File Compression** section
3. Configure:
   - **Enable MP3 compression**: Toggle compression on/off
   - **MP3 Bitrate**: Select quality (128k, 192k, 256k, 320k)
   - **Delete original WAV**: Optionally delete WAV after compression

### Manual Configuration

Edit `config.py` directly:
```python
# Compression settings
ENABLE_COMPRESSION = True
MP3_BITRATE = "192k"  # Options: "128k", "192k", "256k", "320k"
DELETE_ORIGINAL_WAV = False
```

## How It Works

1. **Recording**: Audio is recorded as WAV files (as before)
2. **Saving**: WAV files are saved in 1-hour chunks
3. **Compression**: After each chunk is saved, FFmpeg compresses it to MP3
4. **Cleanup**: If enabled, original WAV files are deleted after successful compression

## Compression Process

- Runs automatically after each recording chunk is saved
- Uses FFmpeg from the `ffmpeg/` directory
- Logs compression progress and file size reduction
- Handles errors gracefully (keeps WAV if compression fails)

## Example Output

```
Compression successful:
  - Original: Rec_20251123_230400_DevStereo_Mix_part1.wav (950.23 MB)
  - Compressed: Rec_20251123_230400_DevStereo_Mix_part1.mp3 (330.45 MB)
  - Reduction: 65.2%
```

## Recommendations

1. **For Radio Recordings**: Use 192kbps (default) - excellent quality with great compression
2. **For Maximum Space Savings**: Use 128kbps - still good quality for voice
3. **For Archival**: Keep `DELETE_ORIGINAL_WAV = False` to preserve original files
4. **For Daily Use**: Set `DELETE_ORIGINAL_WAV = True` to save disk space

## Troubleshooting

### Compression Not Working

1. **Check FFmpeg Path**: Verify `FFMPEG_PATH` in `config.py` points to `ffmpeg.exe`
2. **Check Logs**: Look for compression errors in `recording.log`
3. **Test FFmpeg**: Run `ffmpeg -version` from command line

### Large File Sizes

- Ensure compression is enabled: `ENABLE_COMPRESSION = True`
- Check that MP3 files are being created (look for `.mp3` files)
- Verify bitrate setting is correct

### Compression Takes Too Long

- Compression is done in background after recording
- For 1-hour chunks, compression typically takes 1-2 minutes
- If very slow, consider using 128kbps instead of higher bitrates

## Technical Details

- **Codec**: libmp3lame (MP3 encoder)
- **Format**: MPEG Audio Layer 3
- **Sample Rate**: Preserved from original (44.1kHz)
- **Channels**: Preserved from original (Stereo)

## Notes

- Compression happens automatically - no manual steps required
- Original WAV files are kept by default (unless `DELETE_ORIGINAL_WAV = True`)
- Compression runs after each 1-hour chunk is saved
- If compression fails, original WAV file is preserved

