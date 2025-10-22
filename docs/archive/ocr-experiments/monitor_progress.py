#!/usr/bin/env python3
"""
Monitor processing progress in real-time.

This script checks the checkpoint and log file to report current progress.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import time

COLLECTION_NAME = "teach_like_champion_3_full"
CHECKPOINT_DIR = Path("./checkpoints") / COLLECTION_NAME
LOG_FILE = Path("./processing.log")

def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.2f} hours ({seconds/60:.0f} min)"

def check_checkpoint():
    """Check checkpoint status."""
    if not CHECKPOINT_DIR.exists():
        return None

    # Find checkpoint file
    checkpoint_files = list(CHECKPOINT_DIR.glob("*/checkpoint.json"))
    if not checkpoint_files:
        return None

    checkpoint_file = checkpoint_files[0]

    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)

        return checkpoint_data
    except Exception as e:
        print(f"Warning: Could not read checkpoint: {e}")
        return None

def get_last_log_lines(n=20):
    """Get last N lines from log file."""
    if not LOG_FILE.exists():
        return []

    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            return lines[-n:]
    except Exception:
        return []

def main():
    print("=" * 80)
    print("PROCESSING PROGRESS MONITOR")
    print("=" * 80)
    print()

    # Check if processing is running
    import subprocess
    try:
        result = subprocess.run(
            ["pgrep", "-f", "process_full_document.py"],
            capture_output=True,
            text=True
        )
        is_running = bool(result.stdout.strip())
    except Exception:
        is_running = False

    if is_running:
        print("✓ Processing is RUNNING")
    else:
        print("⚠️  Processing does not appear to be running")
    print()

    # Check checkpoint
    checkpoint = check_checkpoint()

    if checkpoint:
        print("CHECKPOINT STATUS")
        print("-" * 80)
        print(f"  Total pages: {checkpoint.get('total_pages', '?')}")
        print(f"  Processed pages: {checkpoint.get('processed_pages', 0)}")
        print(f"  Last page completed: {checkpoint.get('last_page_completed', -1) + 1}")
        print(f"  File hash: {checkpoint.get('file_hash', 'unknown')[:16]}...")

        # Calculate progress
        total = checkpoint.get('total_pages', 0)
        processed = checkpoint.get('processed_pages', 0)

        if total > 0:
            progress_pct = (processed / total) * 100
            print()
            print(f"  Progress: {progress_pct:.1f}% ({processed}/{total} pages)")

            # Estimate time remaining
            if processed > 0:
                # Get checkpoint timestamps
                page_results = checkpoint.get('page_results', [])
                if page_results:
                    # Estimate based on recent pages
                    # This is rough - better would be to track actual start time
                    print(f"  Pages in checkpoint: {len(page_results)}")

        print()

    else:
        print("NO CHECKPOINT FOUND")
        print("-" * 80)
        print("  Processing may not have started yet, or checkpoints are disabled")
        print()

    # Show recent log activity
    print("RECENT LOG ACTIVITY (last 20 lines)")
    print("-" * 80)

    log_lines = get_last_log_lines(20)
    if log_lines:
        for line in log_lines:
            # Clean up and print
            line = line.rstrip()
            if line:
                print(f"  {line}")
    else:
        print("  No log file found")

    print()
    print("=" * 80)
    print()
    print("Commands:")
    print("  - Monitor continuously: watch -n 10 .venv/bin/python monitor_progress.py")
    print("  - View full log: tail -f processing.log")
    print("  - Kill process: pkill -f process_full_document.py")
    print()

if __name__ == "__main__":
    main()
