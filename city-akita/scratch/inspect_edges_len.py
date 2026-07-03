import os
import sumolib

net_file = "network/akita.net.xml"
if not os.path.exists(net_file):
    print("Network file not found.")
    exit(1)

net = sumolib.net.readNet(net_file)

targets = ["-124579517#0", "-124585729#0"]

print("Upstream Edges of Target branch edges:")
print("="*60)
for edge_id in targets:
    edge = net.getEdge(edge_id)
    if edge is None:
        continue
    print(f"\nTarget Edge: {edge_id} (Length: {edge.getLength():.2f}m)")
    
    # このエッジの始点ノード（流入元）を取得
    from_node = edge.getFromNode()
    print(f"  From Node: {from_node.getID()}")
    
    # そのノードに流入しているエッジをリストアップ（上流エッジ）
    incoming = from_node.getIncoming()
    for up_edge in incoming:
        print(f"    - Upstream Edge ID: {up_edge.getID():<20} | Length: {up_edge.getLength():.2f}m | Lanes: {len(up_edge.getLanes())}")
