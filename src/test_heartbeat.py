#!/usr/bin/env python3
"""
Simple heartbeat test script - prints a message every 5 seconds.
Useful for testing that the environment is working and responsive.
"""

import time
from datetime import datetime


def hb(session_state=None):
    """Print a message every 5 seconds.

    Args:
        session_state: Streamlit session state object to check for cancel flag
    """
    print("=" * 70)
    print("HEARTBEAT TEST - Printing message every 5 seconds")
    print("Press Ctrl+C to stop or click Cancel button")
    print("=" * 70)
    print()

    counter = 0
    try:
        while True:
            # Check if cancel was requested via Streamlit
            if session_state and session_state.get("cancel_requested", False):
                print()
                print("=" * 70)
                print(f"Heartbeat test cancelled by user after {counter} messages")
                print("=" * 70)
                return

            counter += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Heartbeat #{counter} - System is alive! ✓")
            time.sleep(3)

    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print(f"Heartbeat test stopped after {counter} messages")
        print("=" * 70)
