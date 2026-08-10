import os
import time
from pathlib import Path
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

load_dotenv()

HOST    = os.getenv("DATABRICKS_HOST")
TOKEN   = os.getenv("DATABRICKS_TOKEN")
VOLUME  = os.getenv("DATABRICKS_VOLUME")

LOCAL_DIR     = Path("ais_data")
ARCHIVE_DIR   = Path("ais_data/uploaded")
POLL_INTERVAL = 60  # seconds between upload checks

def get_active_filename():
    """Returns the filename currently being written to by the collector."""
    from datetime import datetime, timezone
    ROLLOVER_MINUTES = 15
    now = datetime.now(timezone.utc)
    minute_window = (now.minute // ROLLOVER_MINUTES) * ROLLOVER_MINUTES
    timestamp = now.strftime(f"%Y-%m-%d_%H{minute_window:02d}")
    return f"ais_{timestamp}.jsonl"

def upload_files(client):
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    active = get_active_filename()

    jsonl_files = [
        f for f in LOCAL_DIR.glob("*.jsonl")
        if f.name != active
    ]

    if not jsonl_files:
        print(f"No completed files to upload. Active file: {active}")
        return

    for filepath in jsonl_files:
        volume_path = f"{VOLUME}/{filepath.name}"
        print(f"Uploading {filepath.name} → {volume_path}")

        try:
            with open(filepath, "rb") as f:
                client.files.upload(volume_path, f, overwrite=True)
            print(f"✓ Uploaded {filepath.name}")

            # Move to archive folder locally
            filepath.rename(ARCHIVE_DIR / filepath.name)

        except Exception as e:
            print(f"✗ Failed to upload {filepath.name}: {e}")

def main():
    client = WorkspaceClient(host=HOST, token=TOKEN)
    print(f"Connected to {HOST}")
    print(f"Uploading to Volume: {VOLUME}")
    print(f"Polling every {POLL_INTERVAL} seconds...\n")

    while True:
        upload_files(client)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()