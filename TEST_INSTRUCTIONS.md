# Testing Instructions for Scheduled Recording

This document provides instructions for testing the scheduled recording functionality with a temporary test schedule.

## Current Test Configuration

- **Start Time**: 7:00 AM Phoenix time
- **End Time**: 7:10 AM Phoenix time
- **Duration**: 10 minutes

## Testing Steps

1. **Ensure the application is running before the scheduled start time (7:00 AM)**
   - Launch the application at least 5 minutes before the scheduled start time
   - Verify that the application shows "Scheduled Recording: Active" in the status bar
   - The button should display "Stop Scheduled Recording (TEST MODE)"

2. **Wait for the scheduled recording to start automatically**
   - At 7:00 AM, the recording should start automatically
   - The recording indicator should appear and begin pulsing
   - The status bar should update to show that recording is in progress
   - A log message should appear indicating that scheduled recording has started

3. **Verify recording is working**
   - Check that the audio level meters are showing activity
   - Verify that a file is being created in the output directory with the current date and "_scheduled" suffix
   - The file name format should be: `Coast_to_Coast_YYYYMMDD_070000_scheduled.wav`

4. **Wait for the scheduled recording to stop automatically**
   - At 7:10 AM, the recording should stop automatically
   - The recording indicator should disappear
   - The status bar should update to show that recording has stopped
   - A log message should appear indicating that scheduled recording has stopped

5. **Verify the recorded file**
   - Check that the file exists in the output directory
   - Verify that the file size is appropriate for a 10-minute recording
   - Play back the file to ensure audio was recorded correctly

## Troubleshooting

If the scheduled recording does not start or stop as expected:

1. Check the log file (`recording.log`) for any error messages
2. Verify that the system time is correct and synchronized
3. Ensure that the application has the necessary permissions to create files
4. Check that the stream URL is accessible and working

## Reverting to Original Schedule

After testing is complete, run the `revert_test_schedule.py` script to restore the original schedule:

```
python revert_test_schedule.py
```

This will revert the schedule back to the original 11:06 PM to 3:00 AM schedule.

## Notes

- The test schedule is temporary and is only meant for testing purposes
- The application must be running at the scheduled start time for the recording to begin
- If you close the application before the scheduled end time, the recording will be stopped 