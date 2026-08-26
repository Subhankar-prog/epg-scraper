import urllib.request
import gzip
import xml.etree.ElementTree as ET
import json
import datetime
import os

EPG_URL = "https://github.com/mitthu786/tvepg/releases/download/latest/tataplay.xml.gz"
OUTPUT_FILE = "live_epg.json"

print(f"Downloading EPG from {EPG_URL}...")
try:
    req = urllib.request.Request(EPG_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        compressed_data = response.read()

    print("Decompressing and parsing XML...")
    xml_data = gzip.decompress(compressed_data)
    root = ET.fromstring(xml_data)
except Exception as e:
    print(f"Failed to download or parse EPG: {e}")
    exit(1)

channels = {}
for channel in root.findall('channel'):
    channel_id = channel.get('id')
    display_name_elem = channel.find('display-name')
    if display_name_elem is not None:
        channels[channel_id] = display_name_elem.text

print(f"Found {len(channels)} channels. Processing programmes...")

def parse_xmltv_time(time_str):
    if not time_str: return None
    try:
        dt_str = time_str[:14]
        offset_sign = time_str[15:16] if len(time_str) > 15 else "+"
        offset_hours = int(time_str[16:18]) if len(time_str) > 17 else 0
        offset_mins = int(time_str[18:20]) if len(time_str) > 19 else 0
        
        dt = datetime.datetime.strptime(dt_str, "%Y%m%d%H%M%S")
        offset_td = datetime.timedelta(hours=offset_hours, minutes=offset_mins)
        
        if offset_sign == "+":
            dt = dt - offset_td
        elif offset_sign == "-":
            dt = dt + offset_td
            
        return dt
    except Exception as e:
        return None

now_utc = datetime.datetime.utcnow()
current_programs = {}

for prog in root.findall('programme'):
    channel_id = prog.get('channel')
    start_time = parse_xmltv_time(prog.get('start'))
    stop_time = parse_xmltv_time(prog.get('stop'))
    
    if start_time and stop_time and start_time <= now_utc < stop_time:
        title_elem = prog.find('title')
        if title_elem is not None and title_elem.text:
            channel_name = channels.get(channel_id, channel_id)
            # Store everything lowercase so it's easy to fuzzy-match in JavaScript
            current_programs[channel_name.lower().strip()] = title_elem.text.strip()

print(f"Found {len(current_programs)} currently playing programs.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(current_programs, f, indent=2, ensure_ascii=False)

print(f"Saved to {OUTPUT_FILE}.")
