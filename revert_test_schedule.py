"""
Revert Test Schedule Script

This script reverts the temporary test schedule (7:00 AM to 7:10 AM for 10 minutes)
back to the original schedule (11:06 PM to 3:00 AM for 3 hours and 54 minutes).

Run this script after testing is complete.
"""

import re
import os

def revert_main_py():
    """Revert changes in main.py"""
    with open('main.py', 'r') as file:
        content = file.read()
    
    # Revert recording times
    content = re.sub(
        r'# TEMPORARY TEST CONFIGURATION.*?\n\s*recording_time_start = time\(hour=7, minute=0\).*?\n\s*recording_time_stop = time\(hour=7, minute=10\).*?\n',
        'recording_time_start = time(hour=23, minute=6)  # 11:06 PM\n    recording_time_stop = time(hour=3, minute=0)    # 3:00 AM\n    ',
        content, flags=re.DOTALL
    )
    
    # Revert duration
    content = re.sub(
        r'args=\(filename, 600\),\s*# 10 minutes = 600 seconds \(test duration\)',
        'args=(filename, 14040),  # 3 hours and 54 minutes = 14040 seconds',
        content
    )
    
    # Revert logging messages
    content = re.sub(
        r'logging\.info\("Scheduled recording started \(TEST MODE - 10 minutes\)"\)',
        'logging.info("Scheduled recording started")',
        content
    )
    
    content = re.sub(
        r'logging\.info\("Scheduled recording stopped \(TEST MODE\)"\)',
        'logging.info("Scheduled recording stopped")',
        content
    )
    
    # Revert scheduler jobs
    content = re.sub(
        r'scheduler\.add_job\(\s*start_scheduled,\s*\'cron\',\s*hour=7,\s*minute=0,.*?\)\s*# 7:00 AM \(test time\)',
        'scheduler.add_job(start_scheduled, \'cron\', hour=23, minute=6, id=\'start_scheduled_recording\', replace_existing=True)  # 11:06 PM',
        content, flags=re.DOTALL
    )
    
    content = re.sub(
        r'scheduler\.add_job\(\s*stop_scheduled,\s*\'cron\',\s*hour=7,\s*minute=10,.*?\)\s*# 7:10 AM \(test time\)',
        'scheduler.add_job(stop_scheduled, \'cron\', hour=3, minute=0, id=\'stop_scheduled_recording\', replace_existing=True)  # 3:00 AM',
        content, flags=re.DOTALL
    )
    
    # Revert logging info
    content = re.sub(
        r'f"Schedule set \(TEST MODE\):.*?f"- Duration: 10 minutes \(test duration\)"',
        'f"Schedule set:\\n" \\\nf"- Start: {start_datetime.strftime(\'%Y-%m-%d %H:%M\')} Phoenix time\\n" \\\nf"- Stop: {stop_datetime.strftime(\'%Y-%m-%d %H:%M\')} Phoenix time\\n" \\\nf"- Duration: 3 hours and 54 minutes"',
        content, flags=re.DOTALL
    )
    
    # Revert print message
    content = re.sub(
        r'print\(f"TEST MODE: Scheduled recording set for 7:00 AM to 7:10 AM Phoenix time \(10 minutes\)"\)',
        'print(f"Scheduled recording set for 11:06 PM to 3:00 AM Phoenix time")',
        content
    )
    
    with open('main.py', 'w') as file:
        file.write(content)
    
    print("Reverted main.py to original schedule")

def revert_iheart_gui_py():
    """Revert changes in iheart_gui.py"""
    with open('iheart_gui.py', 'r') as file:
        content = file.read()
    
    # Revert button text
    content = re.sub(
        r'self\.scheduled_record_btn = QPushButton\("Start Scheduled Recording \(TEST: 7:00-7:10 AM\)"\)',
        'self.scheduled_record_btn = QPushButton("Start Scheduled Recording")',
        content
    )
    
    # Revert button text in toggle method
    content = re.sub(
        r'self\.scheduled_record_btn\.setText\("Stop Scheduled Recording \(TEST MODE\)"\)',
        'self.scheduled_record_btn.setText("Stop Scheduled Recording")',
        content
    )
    
    content = re.sub(
        r'self\.scheduled_record_btn\.setText\("Start Scheduled Recording \(TEST: 7:00-7:10 AM\)"\)',
        'self.scheduled_record_btn.setText("Start Scheduled Recording")',
        content
    )
    
    # Revert toggle_scheduled_recording method
    content = re.sub(
        r'self\.log_message\("TEST MODE: Scheduled recording set \(7:00 AM to 7:10 AM Phoenix time - 10 minutes\)"\)',
        'self.log_message("Scheduled recording set (11:06 PM - 3:00 AM Phoenix time)")',
        content
    )
    
    content = re.sub(
        r'# TEMPORARY TEST CONFIGURATION\n\s*start_time = time\(hour=7, minute=0\)\n\s*end_time = time\(hour=7, minute=10\)',
        'start_time = time(hour=23, minute=6)\n                end_time = time(hour=3, minute=0)',
        content
    )
    
    content = re.sub(
        r'if start_time <= now <= end_time:',
        'if start_time <= now or now <= end_time:',
        content
    )
    
    content = re.sub(
        r'next_recording = datetime\.combine\(datetime\.now\(\)\.date\(\), time\(hour=7, minute=0\)\)\n\s*if datetime\.now\(\)\.time\(\) >= time\(hour=7, minute=0\):',
        'next_recording = datetime.combine(datetime.now().date(), time(hour=23, minute=6))\n                    if datetime.now().time() >= time(hour=23, minute=6):',
        content
    )
    
    # Revert update_status method
    content = re.sub(
        r'# TEMPORARY TEST CONFIGURATION\n\s*start_time = time\(hour=7, minute=0\)\n\s*end_time = time\(hour=7, minute=10\)',
        'start_time = time(hour=23, minute=6)\n            end_time = time(hour=3, minute=0)',
        content
    )
    
    content = re.sub(
        r'# TEMPORARY TEST CONFIGURATION\n\s*next_recording = datetime\.combine\(now\.date\(\), time\(hour=7, minute=0\)\)\n\s*if now\.time\(\) >= time\(hour=7, minute=0\):',
        'next_recording = datetime.combine(now.date(), time(hour=23, minute=6))\n        if now.time() >= time(hour=23, minute=6):',
        content
    )
    
    content = re.sub(
        r'f"Next scheduled recording: {next_recording\.strftime\(\'%I:%M %p\'\)} \(TEST MODE - 10 minutes\)"',
        'f"Next scheduled recording: {next_recording.strftime(\'%I:%M %p\')}"',
        content
    )
    
    with open('iheart_gui.py', 'w') as file:
        file.write(content)
    
    print("Reverted iheart_gui.py to original schedule")

if __name__ == "__main__":
    print("Reverting test schedule to original schedule...")
    revert_main_py()
    revert_iheart_gui_py()
    print("Done! Schedule has been reverted to 11:06 PM - 3:00 AM.") 