import os
import sumolib

net_file = "network/akita.net.xml"
if not os.path.exists(net_file):
    print("Network file not found.")
    exit(1)

net = sumolib.net.readNet(net_file)

# ボトルネックTOP 5の交差点情報（順位、交差点番号、SUMO Node ID）
target_junctions = [
    {"rank": 1, "no": "64", "id": "1386236878", "name": "千秋広小路・バイパス方面"},
    {"rank": 2, "no": "63", "id": "1386203158", "name": "茨島・主要部"},
    {"rank": 3, "no": "115", "id": "1386293515", "name": "新国道方面"},
    {"rank": 4, "no": "62", "id": "1386232011", "name": "千秋公園入口・マージ交差点"},
    {"rank": 5, "no": "29", "id": "cluster_1332330172_9242143122", "name": "茨島跨線橋付近"}
]

print("秋田市主要ボトルネック交差点 周辺道路の現在の車線数リスト")
print("="*80)

for j in target_junctions:
    node_id = j["id"]
    print(f"\n[順位 {j['rank']}] 交差点番号: {j['no']} | SUMO Node ID: {node_id} ({j['name']})")
    print("-" * 80)
    
    node = net.getNode(node_id)
    if node is None:
        print("  Node not found in network.")
        continue
        
    incoming = node.getIncoming()
    outgoing = node.getOutgoing()
    
    print("  ■ 流入道路 (Incoming Edges) :")
    for edge in incoming:
        edge_id = edge.getID()
        lanes_count = len(edge.getLanes())
        road_name = edge.getName() or "Unknown Street"
        print(f"    - Edge ID: {edge_id:<20} | 現在の車線数: {lanes_count} | 道路名: {road_name}")
        
    print("  ■ 流出道路 (Outgoing Edges) :")
    for edge in outgoing:
        edge_id = edge.getID()
        lanes_count = len(edge.getLanes())
        road_name = edge.getName() or "Unknown Street"
        print(f"    - Edge ID: {edge_id:<20} | 現在の車線数: {lanes_count} | 道路名: {road_name}")
