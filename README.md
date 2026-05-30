# ScreenMindr — Desktop Usage Tracker

A Windows desktop productivity tracker that monitors active applications, aggregates daily usage time and visualizes patterns.

## Features
- Tracks active window/app usage
- Stores daily usage data
- Generates productivity summaries
- Visualizes usage patterns with charts
- Sends reminders/notifications

## Tech Stack
- Python
- pywin32
- psutil
- matplotlib
- plyer

## Architecture

To run this project you need to:
1. Install the following modules with pip (open a terminal in the project folder and run pip install followed by following modules)
    - pywin32
    - win32gui
    - win32process
    - keyboard
    - psutil
    - ctypes
    - plyer
    - matplotlib
2. Create a config.txt file in the ./src/ directory
3. run python ./process_time.py
4. Enjoy :)
