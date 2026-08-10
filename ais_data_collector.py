import asyncio
import websockets
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("AIS_API_KEY")
print(API_KEY)
OUTPUT_DIR = Path("ais_data")       # folder where JSONL files land
ROLLOVER_MINUTES = 15               # new file every 15 minutes

def get_output_path():
    """Generate a timestamped filename for the current rollover window."""
    now = datetime.now(timezone.utc)
    # Round down to nearest 15-minute window
    minute_window = (now.minute // ROLLOVER_MINUTES) * ROLLOVER_MINUTES
    timestamp = now.strftime(f"%Y-%m-%d_%H{minute_window:02d}")
    return OUTPUT_DIR / f"ais_{timestamp}.jsonl"

async def connect_ais_stream():
    OUTPUT_DIR.mkdir(exist_ok=True)

    subscribe_message = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[37.4, -122.7], [38.0, -122.0]]],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
    }

    current_file_path = None
    outfile = None

    try:
        async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
            print(f"[{datetime.now(timezone.utc)}] Connected to aisstream.io")
            await websocket.send(json.dumps(subscribe_message))
            print(f"[{datetime.now(timezone.utc)}] Subscribed. Listening for SF Bay cargo traffic...")

            async for message_json in websocket:
                message = json.loads(message_json)
                msg_type = message.get("MessageType")

                # Only process message types we care about
                if msg_type not in ("PositionReport", "ShipStaticData"):
                    continue

                # Check if we need to roll over to a new file
                new_path = get_output_path()
                if new_path != current_file_path:
                    if outfile:
                        outfile.close()
                        print(f"[{datetime.now(timezone.utc)}] Rolled over to {new_path.name}")
                    current_file_path = new_path
                    outfile = open(current_file_path, "a", encoding="utf-8")

                # Write the record
                record = {
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "message_type": msg_type,
                    "mmsi": message.get("MetaData", {}).get("MMSI"),
                    "ship_name": message.get("MetaData", {}).get("ShipName", "").strip(),
                    "raw": message
                }
                outfile.write(json.dumps(record) + "\n")
                outfile.flush()  # ensure it's written to disk immediately

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"[{datetime.now(timezone.utc)}] Connection lost: {e}. Reconnecting in 10s...")
        await asyncio.sleep(10)
    finally:
        if outfile:
            outfile.close()

async def main():
    """Run the collector forever, reconnecting on disconnect."""
    while True:
        await connect_ais_stream()

if __name__ == "__main__":
    asyncio.run(main())