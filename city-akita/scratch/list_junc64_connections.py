import os
import xml.etree.ElementTree as ET

net_file = "network/akita.net.xml"
if not os.path.exists(net_file):
    print("Network not found.")
    exit(1)

tree = ET.parse(net_file)
root = tree.getroot()

print("Current Connections for Junction 1386236878:")
print("="*80)
for conn in root.findall("connection"):
    tl = conn.get("tl")
    if tl == "1386236878":
        print(f"From: {conn.get('from'):<30} (lane {conn.get('fromLane')}) | To: {conn.get('to'):<30} (lane {conn.get('toLane')}) | Dir: {conn.get('dir')}")
