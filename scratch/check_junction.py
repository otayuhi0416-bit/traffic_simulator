import xml.etree.ElementTree as ET
import os

net_file = r"c:\Users\Genno_Shirou\Documents\works\traffic_simulator\city-akita\network\akita.net.xml"
if not os.path.exists(net_file):
    print("Network file not found!")
    exit(1)

tree = ET.parse(net_file)
root = tree.getroot()

j_id = "1386150782"

# 交差点の情報を表示
print("=== JUNCTION ===")
for j in root.findall("junction"):
    if j.get("id") == j_id:
        print(f"Junction ID: {j.get('id')}, Type: {j.get('type')}, incLanes: {j.get('incLanes')}, intLanes: {j.get('intLanes')}")
        # print(ET.tostring(j, encoding='utf-8').decode('utf-8'))

# 流入エッジ
print("=== INCOMING EDGES ===")
inc_edges = []
for edge in root.findall("edge"):
    if edge.get("to") == j_id:
        lanes = edge.findall("lane")
        print(f"Edge ID: {edge.get('id')}, numLanes: {len(lanes)}")
        for l in lanes:
            print(f"  Lane ID: {l.get('id')}, index: {l.get('index')}, shape: {l.get('shape')}")
        inc_edges.append(edge.get("id"))

# 流出エッジ
print("=== OUTGOING EDGES ===")
out_edges = []
for edge in root.findall("edge"):
    if edge.get("from") == j_id:
        lanes = edge.findall("lane")
        print(f"Edge ID: {edge.get('id')}, numLanes: {len(lanes)}")
        for l in lanes:
            print(f"  Lane ID: {l.get('id')}, index: {l.get('index')}, shape: {l.get('shape')}")
        out_edges.append(edge.get("id"))

# 接続(connection)を表示
print("=== CONNECTIONS ===")
for conn in root.findall("connection"):
    if conn.get("from") in inc_edges:
        print(f"Conn: from={conn.get('from')} (lane={conn.get('fromLane')}) -> to={conn.get('to')} (lane={conn.get('toLane')}) dir={conn.get('dir')}")
