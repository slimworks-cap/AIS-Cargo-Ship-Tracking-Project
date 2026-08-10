import streamlit as st
import pandas as pd
import json
import time
from databricks import sql
from dotenv import load_dotenv
import os

load_dotenv()

HOST      = os.getenv("DATABRICKS_HOST")
TOKEN     = os.getenv("DATABRICKS_TOKEN")
HTTP_PATH = os.getenv("SQL_WAREHOUSE_HTTPS")

st.set_page_config(
    page_title="SF Bay Cargo Tracker",
    page_icon="🚢",
    layout="wide"
)

st.title("🚢 SF Bay Cargo Vessel Tracker")
st.caption("Live cargo vessel positions from AIS stream via Databricks Gold table")

@st.cache_data(ttl=300)  # refresh data every 5 minutes
def load_vessels():
    connection = sql.connect(
        server_hostname=HOST.replace("https://", ""),
        http_path=HTTP_PATH,
        access_token=TOKEN
    )
    cursor = connection.cursor()
    cursor.execute("""
        WITH deduped AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY mmsi ORDER BY received_at DESC) AS row_num
            FROM cargo_tracker.ais_data.gold_cargo_vessels
        )
        SELECT
            mmsi,
            ship_name,
            latitude,
            longitude,
            speed_knots,
            course,
            nav_status,
            ship_type,
            destination,
            call_sign,
            imo_number,
            received_at
        FROM deduped
        WHERE row_num = 1
    """)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    cursor.close()
    connection.close()
    return pd.DataFrame(rows, columns=cols)

# Load data
df = load_vessels()

# Sidebar metrics
st.sidebar.header("Fleet Summary")
st.sidebar.metric("Total Cargo Vessels", len(df))
st.sidebar.metric("Underway", len(df[df["nav_status"] == 0]))
st.sidebar.metric("At Anchor", len(df[df["nav_status"] == 1]))
st.sidebar.metric("Moored", len(df[df["nav_status"] == 5]))

# Sidebar filters
st.sidebar.header("Filters")
status_options = {
    "All": None,
    "Underway only": 0,
    "At anchor only": 1,
    "Moored only": 5
}
selected_status = st.sidebar.selectbox("Navigation Status", list(status_options.keys()))
if status_options[selected_status] is not None:
    df = df[df["nav_status"] == status_options[selected_status]]

type_filter = st.sidebar.multiselect(
    "Ship Type",
    options=sorted(df["ship_type"].dropna().unique().tolist()),
    default=sorted(df["ship_type"].dropna().unique().tolist())
)
if type_filter:
    df = df[df["ship_type"].isin(type_filter)]

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing {len(df)} vessels")

# Build GeoJSON for the map
features = []
for _, row in df.iterrows():
    if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]]
            },
            "properties": {
                "mmsi": str(row["mmsi"]),
                "ship_name": str(row["ship_name"] or "").strip(),
                "speed_knots": row["speed_knots"],
                "course": row["course"],
                "nav_status": row["nav_status"],
                "ship_type": row["ship_type"],
                "destination": str(row["destination"] or "").strip(),
                "call_sign": str(row["call_sign"] or "").strip(),
                "received_at": str(row["received_at"])
            }
        })

geojson = json.dumps({"type": "FeatureCollection", "features": features})

# Render the map using Leaflet via HTML component
map_html = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css"/>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <style>
        #map {{ height: 580px; width: 100%; border-radius: 8px; }}
        .vessel-popup {{ font-family: sans-serif; font-size: 13px; min-width: 180px; }}
        .vessel-popup b {{ font-size: 14px; }}
    </style>
</head>
<body>
<div id="map"></div>
<script>
    const map = L.map('map').setView([37.80, -122.35], 11);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        subdomains: 'abcd', maxZoom: 19
    }}).addTo(map);

    const geojson = {geojson};
    const statusColors = {{ 0: '#F28C38', 1: '#534AB7', 5: '#2ECC71' }};

    L.geoJSON(geojson, {{
        pointToLayer: function(feature, latlng) {{
            const p = feature.properties;
            const color = statusColors[p.nav_status] || '#999999';
            return L.circleMarker(latlng, {{
                radius: 7,
                fillColor: color,
                color: color,
                weight: 1,
                fillOpacity: 0.85
            }});
        }},
        onEachFeature: function(feature, layer) {{
            const p = feature.properties;
            layer.bindPopup(`
                <div class="vessel-popup">
                    <b>${{p.ship_name || 'Unknown'}}</b><br>
                    <hr style="margin:4px 0">
                    MMSI: ${{p.mmsi}}<br>
                    Type: ${{p.ship_type}}<br>
                    Speed: ${{p.speed_knots}} kn<br>
                    Course: ${{p.course}}°<br>
                    Destination: ${{p.destination || 'N/A'}}<br>
                    Call Sign: ${{p.call_sign || 'N/A'}}<br>
                    Last seen: ${{p.received_at}}
                </div>
            `);
        }}
    }}).addTo(map);
</script>
</body>
</html>
"""

st.components.v1.html(map_html, height=600)

# Vessel data table below the map
st.subheader("Vessel Details")
st.dataframe(
    df[["ship_name", "mmsi", "ship_type", "destination", 
        "speed_knots", "nav_status", "received_at"]]
    .sort_values("ship_name")
    .reset_index(drop=True),
    use_container_width=True
)

# Auto refresh
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("Data refreshes automatically every 5 minutes")

import pydeck as pdk

st.markdown("---")
st.subheader("🎬 Vessel Movement Animation")
st.caption("Animated trails showing cargo vessel paths over your collection period")

@st.cache_data(ttl=300)
def load_history():
    connection = sql.connect(
        server_hostname=HOST.replace("https://", ""),
        http_path=HTTP_PATH,
        access_token=TOKEN
    )
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            mmsi,
            ship_name,
            longitude,
            latitude,
            received_at,
            CAST(unix_timestamp(received_at) AS BIGINT) * 1000 AS timestamp_ms
        FROM cargo_tracker.ais_data.gold_cargo_history
        ORDER BY mmsi, received_at
    """)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    cursor.close()
    connection.close()
    return pd.DataFrame(rows, columns=cols)

history_df = load_history()

# Sidebar vessel selector for animation
st.sidebar.markdown("---")
st.sidebar.header("Animation")
vessel_options = (history_df
    .groupby(["mmsi", "ship_name"])
    .size()
    .reset_index(name="fixes")
    .sort_values("fixes", ascending=False)
)
vessel_labels = {
    row["ship_name"].strip(): row["mmsi"]
    for _, row in vessel_options.iterrows()
}
selected_vessels = st.sidebar.multiselect(
    "Select vessels to animate",
    options=list(vessel_labels.keys()),
    default=list(vessel_labels.keys())[:5]  # top 5 by default
)

# Filter history to selected vessels
selected_mmsis = [vessel_labels[v] for v in selected_vessels]
filtered_history = history_df[history_df["mmsi"].isin(selected_mmsis)].copy()

if not filtered_history.empty:
    # Build trip data — pydeck expects list of [lon, lat, timestamp_ms] per vessel
    trips = []
    colors = [
        [255, 140, 0],    # orange
        [83, 74, 183],    # purple
        [46, 204, 113],   # green
        [231, 76, 60],    # red
        [52, 152, 219],   # blue
        [155, 89, 182],   # violet
        [241, 196, 15],   # yellow
        [26, 188, 156],   # teal
    ]
    for i, mmsi in enumerate(selected_mmsis):
        vessel_df = filtered_history[filtered_history["mmsi"] == mmsi].copy()
        vessel_df = vessel_df.sort_values("received_at")
        waypoints = vessel_df[["longitude", "latitude", "timestamp_ms"]].values.tolist()
        if len(waypoints) >= 2:
            trips.append({
                "waypoints": waypoints,
                "color": colors[i % len(colors)],
                "name": selected_vessels[i]
            })

    # Time range for animation
    min_ts = int(filtered_history["timestamp_ms"].min())
    max_ts = int(filtered_history["timestamp_ms"].max())

    # Build path data for PathLayer
    paths = []
    for i, mmsi in enumerate(selected_mmsis):
        vessel_df = filtered_history[filtered_history["mmsi"] == mmsi].copy()
        vessel_df = vessel_df.sort_values("received_at")
        coordinates = vessel_df[["longitude", "latitude"]].values.tolist()
        if len(coordinates) >= 2:
            paths.append({
                "path": coordinates,
                "name": selected_vessels[i],
                "color": colors[i % len(colors)]
            })

    path_layer = pdk.Layer(
        "PathLayer",
        paths,
        get_path="path",
        get_color="color",
        get_width=3,
        width_min_pixels=2,
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=37.80,
        longitude=-122.32,
        zoom=11,
        pitch=0
    )

    deck = pdk.Deck(
        layers=[path_layer],
        initial_view_state=view_state,
        map_style=None,
        tooltip={"text": "{name}"}
    )

    st.pydeck_chart(deck)
    st.caption(f"Showing {len(paths)} vessel tracks — {len(filtered_history):,} position fixes")

else:
    st.info("Select at least one vessel from the sidebar to animate.")