#!/usr/bin/env python3
"""
Simple heartbeat test script - prints a message every 5 seconds.
Useful for testing that the environment is working and responsive.
"""

import time
from datetime import datetime


def main():
    """Print a message every 5 seconds."""
    print("=" * 70)
    print("HEARTBEAT TEST - Printing message every 5 seconds")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    counter = 0
    try:
        while True:
            counter += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Heartbeat #{counter} - System is alive! ✓")
            time.sleep(5)

    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print(f"Heartbeat test stopped after {counter} messages")
        print("=" * 70)


if __name__ == "__main__":
    main()
