import xml.etree.ElementTree as ET
import urllib.request
import gzip
import json
import datetime
import os

EPG_URLS = [
    "https://raw.githubusercontent.com/mitthu786/tvepg/main/tataplay/epg.xml.gz",
    "https://raw.githubusercontent.com/mitthu786/tvepg/main/jiotv/epg.xml.gz"
]
OUTPUT_FILE = "live_epg.json"

current_programs = {}
total_channels = 0

for epg_url in EPG_URLS:
    print(f"Downloading EPG from {epg_url}...")
    try:
        req = urllib.request.Request(epg_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            compressed_data = response.read()

        print(f"Decompressing and parsing XML for {epg_url.split('/')[-2]}...")
        xml_data = gzip.decompress(compressed_data)
        root = ET.fromstring(xml_data)

        channels = {}
        for channel in root.findall("channel"):
            ch_id = channel.get("id")
            display_name_elem = channel.find("display-name")
            if ch_id and display_name_elem is not None:
                channels[ch_id] = display_name_elem.text

        total_channels += len(channels)

        now_utc = datetime.datetime.utcnow()
        now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
        current_time_str = now_ist.strftime("%Y%m%d%H%M%S +0530")

        for programme in root.findall("programme"):
            start_time = programme.get("start")
            stop_time = programme.get("stop")
            
            if start_time and stop_time and start_time <= current_time_str <= stop_time:
                channel_id = programme.get("channel")
                title_elem = programme.find("title")
                
                if channel_id and title_elem is not None:
                    channel_name = channels.get(channel_id, channel_id)
                    current_programs[channel_name.lower().strip()] = title_elem.text.strip()
    except Exception as e:
        print(f"Error processing {epg_url}: {e}")

print(f"Found {total_channels} total channels across providers.")
print(f"Found {len(current_programs)} currently playing programs.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(current_programs, f, ensure_ascii=False, indent=2)
